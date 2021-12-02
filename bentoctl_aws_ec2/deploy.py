import os
import shutil

from bentoml.saved_bundle import load_bento_service_metadata

from .ec2 import (
    generate_cloudformation_template_file,
    generate_docker_image_tag,
    generate_ec2_resource_names,
    generate_user_data_script,
)
from .utils import (
    build_docker_image,
    console,
    create_ecr_repository_if_not_exists,
    get_ecr_login_info,
    push_docker_image_to_repository,
    run_shell_command,
)


def deploy(bento_path, deployment_name, deployment_spec):
    bento_metadata = load_bento_service_metadata(bento_path)

    (
        template_name,
        stack_name,
        repo_name,
        elb_name,
    ) = generate_ec2_resource_names(deployment_name)

    # make deployable folder and overide if found according to user pref
    project_path = os.path.join(
        os.path.curdir, f"{bento_metadata.name}-{bento_metadata.version}-deployable"
    )
    try:
        os.mkdir(project_path)
    except FileExistsError:
        response = console.input(
            f"Existing deployable [[b]{project_path}[/b]] found! Override? (y/n): "
        )
        if response.lower() in ["yes", "y", ""]:
            print("overiding existing deployable!")
            shutil.rmtree(project_path)
            os.mkdir(project_path)
        elif response.lower() in ["no", "n"]:
            print("Using existing deployable!")

    with console.status("Building image"):
        repository_id, registry_url = create_ecr_repository_if_not_exists(
            deployment_spec["region"], repo_name
        )
        _, username, password = get_ecr_login_info(
            deployment_spec["region"], repository_id
        )
        ecr_tag = generate_docker_image_tag(
            registry_url, bento_metadata.name, bento_metadata.version
        )
        build_docker_image(context_path=bento_path, image_tag=ecr_tag)

    with console.status("Pushing image to ECR"):
        push_docker_image_to_repository(
            repository=ecr_tag, username=username, password=password
        )
    console.print(f"Image built and pushed [[b]{registry_url}[/b]]")

    encoded_user_data = generate_user_data_script(
        registry=registry_url,
        image_tag=ecr_tag,
        region=deployment_spec["region"],
        env_vars=deployment_spec.get("environment_variables", {}),
        enable_gpus=deployment_spec.get("enable_gpus", False),
    )

    file_path = generate_cloudformation_template_file(
        project_dir=project_path,
        user_data=encoded_user_data,
        sam_template_name=template_name,
        elb_name=elb_name,
        ami_id=deployment_spec["ami_id"],
        instance_type=deployment_spec["instance_type"],
        autoscaling_min_size=deployment_spec["ec2_auto_scale"]["min_size"],
        autoscaling_desired_capacity=deployment_spec["ec2_auto_scale"][
            "desired_capacity"
        ],
        autoscaling_max_size=deployment_spec["ec2_auto_scale"]["max_size"],
        health_check_path=deployment_spec["elastic_load_balancing"][
            "health_check_path"
        ],
        health_check_port=deployment_spec["elastic_load_balancing"][
            "health_check_port"
        ],
        health_check_interval_seconds=deployment_spec["elastic_load_balancing"][
            "health_check_interval_seconds"
        ],
        health_check_timeout_seconds=deployment_spec["elastic_load_balancing"][
            "health_check_timeout_seconds"
        ],
        healthy_threshold_count=deployment_spec["elastic_load_balancing"][
            "healthy_threshold_count"
        ],
    )
    copied_env = os.environ.copy()
    copied_env["AWS_DEFAULT_REGION"] = deployment_spec["region"]
    console.print(f"Generated CF template [[b]{file_path}[/b]]")

    with console.status("Building CF template"):
        run_shell_command(
            command=["sam", "build", "-t", template_name],
            cwd=project_path,
            env=copied_env,
        )
        run_shell_command(
            command=[
                "sam",
                "package",
                "--output-template-file",
                "packaged.yaml",
            ],
            cwd=project_path,
            env=copied_env,
        )
        console.print("Built CF template")

    with console.status("Deploying to EC2"):
        run_shell_command(
            command=[
                "sam",
                "deploy",
                "--template-file",
                "packaged.yaml",
                "--stack-name",
                stack_name,
                "--capabilities",
                "CAPABILITY_IAM",
            ],
            cwd=project_path,
            env=copied_env,
        )
