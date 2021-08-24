import os
import sys
import shutil

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
from deploy import deploy


def update(bento_bundle_path, deployment_name, config_json):
    """
    The deployment operation can also be used for updation since we are using
    AWS Sam cli for managing deployments.
    """
    try:
        deploy(bento_bundle_path, deployment_name, config_json)
        return 0
    except Exception as e:
        print(e)
        return 1


if __name__ == "__main__":
    if len(sys.argv) != 4:
        raise Exception(
            "Please provide bento_bundle_path deployment_name and configuration json"
        )
    bento_bundle_path = sys.argv[1]
    deployment_name = sys.argv[2]
    config_json = sys.argv[3] if sys.argv[3] else "ec2_config.json"

    return_code = update(bento_bundle_path, deployment_name, config_json)
    if return_code == 0:
        console.print("[bold green]Update Complete!")
    if return_code == 1:
        console.print("Updation unsuccessful!")
