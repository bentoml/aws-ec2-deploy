from .deploy import deploy


def update(bento_bundle_path, deployment_name, ec2_json):
    """
    The deployment operation can also be used for updation since we are using
    AWS Sam cli for managing deployments.
    """
    deploy(bento_bundle_path, deployment_name, ec2_json)
