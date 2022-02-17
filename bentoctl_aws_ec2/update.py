from .deploy import deploy


def update(bento_path, deployment_name, deployment_spec):
    """
    The deployment operation can also be used for updation since we are using
    AWS Cloudformation for managing deployments.
    """
    return deploy(bento_path, deployment_name, deployment_spec)
