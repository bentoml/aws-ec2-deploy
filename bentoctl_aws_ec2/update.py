from .deploy import deploy


def update(bento_path, deployment_name, deployment_spec):
    """
    The deployment operation can also be used for updation since we are using
    AWS Sam cli for managing deployments.
    """
    deploy(bento_path, deployment_name, deployment_spec)
