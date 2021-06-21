import os
import sys
from bentoml.saved_bundle import load_bento_service_metadata
from utils import (
    get_configuration_value,
    create_ecr_repository_if_not_exists,
    get_ecr_login_info,
    build_docker_image,
    push_docker_image_to_repository,
    create_s3_bucket_if_not_exists,
    run_shell_command,
)
from ec2 import (
    generate_docker_image_tag,
    generate_ec2_resource_names,
    generate_user_data_script,
    generate_cloudformation_template_file,
)


def deploy_to_ec2(bento_bundle_path, deployment_name, config_json):
    bento_metadata = load_bento_service_metadata(bento_bundle_path)

    ec2_config = get_configuration_value(config_json)
    (
        template_name,
        stack_name,
        s3_bucket_name,
        repo_name,
        elb_name,
    ) = generate_ec2_resource_names(deployment_name)

    print("Creating S3 bucket for cloudformation")
    create_s3_bucket_if_not_exists(s3_bucket_name, ec2_config["region"])

    print("Build and push image to ECR")
    repository_id, registry_url = create_ecr_repository_if_not_exists(
        ec2_config["region"], repo_name
    )
    _, username, password = get_ecr_login_info(ec2_config["region"], repository_id)
    ecr_tag = generate_docker_image_tag(
        registry_url, bento_metadata.name, bento_metadata.version
    )
    build_docker_image(context_path=bento_bundle_path, image_tag=ecr_tag)
    push_docker_image_to_repository(
        repository=ecr_tag, username=username, password=password
    )
    print("Generate CF template")
    encoded_user_data = generate_user_data_script(
        registry=registry_url, image_tag=ecr_tag, region=ec2_config["region"],
    )
    project_path = os.path.join(
        os.path.curdir, f"{bento_metadata.name}-{bento_metadata.version}-deployable"
    )
    os.mkdir(project_path)
    generate_cloudformation_template_file(
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

    print("Build CF template")
    run_shell_command(
        command=["sam", "build", "-t", template_name], cwd=project_path, env=copied_env,
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
    print("Deploy EC2")
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
    if len(sys.argv) != 4:
        raise Exception(
            "Please provide bento_bundle_path deployment_name and configuration json"
        )
    bento_bundle_path = sys.argv[1]
    deployment_name = sys.argv[2]
    config_json = sys.argv[3] if sys.argv[3] else "ec2_config.json"

    deploy_to_ec2(bento_bundle_path, deployment_name, config_json)
