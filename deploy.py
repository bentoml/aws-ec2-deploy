import os
import sys
import shutil
import argparse

from bentoml.saved_bundle import load_bento_service_metadata
from utils import (
    get_configuration_value,
    create_ecr_repository_if_not_exists,
    get_ecr_login_info,
    build_docker_image,
    push_docker_image_to_repository,
    create_s3_bucket_if_not_exists,
    run_shell_command,
    console,
)
from ec2 import (
    generate_docker_image_tag,
    generate_ec2_resource_names,
    generate_user_data_script,
    generate_cloudformation_template_file,
)


def deploy(bento_bundle_path, deployment_name, config_json):
    bento_metadata = load_bento_service_metadata(bento_bundle_path)

    ec2_config = get_configuration_value(config_json)
    (
        template_name,
        stack_name,
        s3_bucket_name,
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

    create_s3_bucket_if_not_exists(s3_bucket_name, ec2_config["region"])
    console.print(f"S3 bucket for cloudformation created [[b]{s3_bucket_name}[/b]]")

    with console.status("Building image"):
        repository_id, registry_url = create_ecr_repository_if_not_exists(
            ec2_config["region"], repo_name
        )
        _, username, password = get_ecr_login_info(ec2_config["region"], repository_id)
        ecr_tag = generate_docker_image_tag(
            registry_url, bento_metadata.name, bento_metadata.version
        )
        build_docker_image(context_path=bento_bundle_path, image_tag=ecr_tag)

    with console.status("Pushing image to ECR"):
        push_docker_image_to_repository(
            repository=ecr_tag, username=username, password=password
        )
    console.print(f"Image built and pushed [[b]{registry_url}[/b]]")

    encoded_user_data = generate_user_data_script(
        registry=registry_url,
        image_tag=ecr_tag,
        region=ec2_config["region"],
        env_vars=ec2_config.get("environment_variables", {}),
        enable_gpus=ec2_config.get('enable_gpus', False),
    )

    file_path = generate_cloudformation_template_file(
        project_dir=project_path,
        user_data=encoded_user_data,
        s3_bucket_name=s3_bucket_name,
        sam_template_name=template_name,
        elb_name=elb_name,
        ami_id=ec2_config["ami_id"],
        instance_type=ec2_config["instance_type"],
        autoscaling_min_size=ec2_config["ec2_auto_scale"]["min_size"],
        autoscaling_desired_capacity=ec2_config["ec2_auto_scale"]["desired_capacity"],
        autoscaling_max_size=ec2_config["ec2_auto_scale"]["max_size"],
        health_check_path=ec2_config["elb"]["health_check_path"],
        health_check_port=ec2_config["elb"]["health_check_port"],
        health_check_interval_seconds=ec2_config["elb"][
            "health_check_interval_seconds"
        ],
        health_check_timeout_seconds=ec2_config["elb"]["health_check_timeout_seconds"],
        healthy_threshold_count=ec2_config["elb"]["healthy_threshold_count"],
    )
    copied_env = os.environ.copy()
    copied_env["AWS_DEFAULT_REGION"] = ec2_config["region"]
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
                "--s3-bucket",
                s3_bucket_name,
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
                "--s3-bucket",
                s3_bucket_name,
            ],
            cwd=project_path,
            env=copied_env,
        )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Deploy the bentoml bundle on EC2",
        epilog="Check out https://github.com/bentoml/aws-ec2-deploy#readme to know more",
    )
    parser.add_argument("bento_bundle_path", help="Path to bentoml bundle")
    parser.add_argument(
        "deployment_name", help="The name you want to use for your deployment"
    )
    parser.add_argument(
        "config_json",
        help="(optional) The config file for your deployment",
        default=os.path.join(os.getcwd(), "ec2_config.json"),
        nargs="?",
    )
    args = parser.parse_args()

    deploy(args.bento_bundle_path, args.deployment_name, args.config_json)
    console.print("[bold green]Deployment Complete!")
