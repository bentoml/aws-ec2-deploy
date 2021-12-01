import boto3
from botocore.exceptions import ClientError

from .ec2 import generate_ec2_resource_names
from .utils import console


def delete(deployment_name, ec2_config):
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
