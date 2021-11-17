import boto3
from botocore.exceptions import ClientError

from .ec2 import generate_ec2_resource_names
from .utils import get_configuration_value, console


def delete(deployment_name, config_json):
    ec2_config = get_configuration_value(config_json)
    _, stack_name, s3_bucket_name, repo_name, _ = generate_ec2_resource_names(
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

    # delete s3 bucket
    s3_client = boto3.client("s3", ec2_config["region"])
    s3 = boto3.resource("s3")
    try:
        console.print(f"Delete S3 bucket [b]{s3_bucket_name}[/b]")
        s3.Bucket(s3_bucket_name).objects.all().delete()
        s3_client.delete_bucket(Bucket=s3_bucket_name)
    except ClientError as e:
        if e.response and e.response["Error"]["Code"] != "NoSuchBucket":
            # If there is no bucket, we just let it silently fail, don't have to do
            # any thing
            raise e
