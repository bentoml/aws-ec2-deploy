import sys
import boto3
from botocore.exceptions import ClientError

from ec2 import generate_ec2_resource_names
from utils import get_configuration_value


def delete_deployment(deployment_name, config_json):
    ec2_config = get_configuration_value(config_json)
    _, stack_name, s3_bucket_name, repo_name, _ = generate_ec2_resource_names(deployment_name)
    cf_client = boto3.client("cloudformation", ec2_config['region'])
    print(f'Delete CloudFormation Stack {stack_name}')
    cf_client.delete_stack(StackName=stack_name)

    # delete ecr repository
    print('Delete ECR repo')
    ecr_client = boto3.client('ecr', ec2_config['region'])
    try:
        print(f'Delete ECR repo {repo_name}')
        ecr_client.delete_repository(repositoryName=repo_name, force=True)
    except ClientError as e:
        # raise error, if the repo can't be found
        if e.response and e.response['Error']['Code'] != 'RepositoryNotFoundException':
            raise e

    # delete s3 bucket
    s3_client = boto3.client('s3', ec2_config['region'])
    s3 = boto3.resource('s3')
    try:
        print(f'Delete S3 bucket {s3_bucket_name}')
        s3.Bucket(s3_bucket_name).objects.all().delete()
        s3_client.delete_bucket(Bucket=s3_bucket_name)
    except ClientError as e:
        if e.response and e.response['Error']['Code'] != 'NoSuchBucket':
            # If there is no bucket, we just let it silently fail, don't have to do
            # any thing
            raise e


if __name__ == '__main__':
    if len(sys.argv) != 3:
        raise Exception(
            'Please provide deployment_name and configuration json as parameters'
        )
    deployment_name = sys.argv[1]
    config_json = sys.argv[2] if sys.argv[2] else 'ec2_config.json'

    delete_deployment(deployment_name, config_json)
