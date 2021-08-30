import sys
import argparse
import os

from utils import console
from deploy import deploy


def update(bento_bundle_path, deployment_name, config_json):
    """
    The deployment operation can also be used for updation since we are using
    AWS Sam cli for managing deployments.
    """
    deploy(bento_bundle_path, deployment_name, config_json)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Update the bentoml bundle deployed on EC2",
        epilog="Check out https://github.com/bentoml/aws-ec2-deploy#readme to know more",
    )
    parser.add_argument("bento_bundle_path", help="Path to bentoml bundle.")
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

    try:
        update(args.bento_bundle_path, args.deployment_name, args.config_json)
    except Exception as e:
        print(e)
        console.print("Updation unsuccessful!")
    else:
        console.print("[bold green]Update Complete!")
