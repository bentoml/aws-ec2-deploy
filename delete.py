import os
import argparse

import boto3
from botocore.exceptions import ClientError

from ec2 import generate_ec2_resource_names
from utils import get_configuration_value, console


def delete(deployment_name, config_json):
    ec2_config = get_configuration_value(config_json)
    _, stack_name, repo_name, _ = generate_ec2_resource_names(
        deployment_name
    )
    cf_client = boto3.client("cloudformation", ec2_config["region"])
    console.print(f"Delete CloudFormation Stack [b]{stack_name}[/b]")
    cf_client.delete_stack(StackName=stack_name)

    # delete ecr repository
    ecr_client = boto3.client("ecr", ec2_config["region"])
    try:
        console.print(f"Delete ECR repo [b]{repo_name}[/b]")
        ecr_client.delete_repository(repositoryName=repo_name, force=True)
    except ClientError as e:
        # raise error, if the repo can't be found
        if e.response and e.response["Error"]["Code"] != "RepositoryNotFoundException":
            raise e


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Delete the bundle deployed on EC2",
        epilog="Check out https://github.com/bentoml/aws-ec2-deploy#readme to know more",
    )
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

    delete(args.deployment_name, args.config_json)
    console.print(f"[bold green]Deleted {args.deployment_name}!")
