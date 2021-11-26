import os
import re
import base64

from bentoctl_aws_ec2.ec2.user_data_template import EC2_USER_INIT_SCRIPT
from bentoctl_aws_ec2.ec2.ec2_cloudformation_template import EC2_CLOUDFORMATION_TEMPLATE


def generate_aws_compatible_string(*items, max_length=63):
    """
    Generate a AWS resource name that is composed from list of string items. This
    function replaces all invalid characters in the given items into '-', and allow user
    to specify the max_length for each part separately by passing the item and its max
    length in a tuple, e.g.:

    >> generate_aws_compatible_string("abc", "def")
    >> 'abc-def'  # concatenate multiple parts

    >> generate_aws_compatible_string("abc_def")
    >> 'abc-def'  # replace invalid chars to '-'

    >> generate_aws_compatible_string(("ab", 1), ("bcd", 2), max_length=4)
    >> 'a-bc'  # trim based on max_length of each part
    """
    trimmed_items = [
        item[0][: item[1]] if type(item) == tuple else item for item in items
    ]
    items = [item[0] if type(item) == tuple else item for item in items]

    for i in range(len(trimmed_items)):
        if len("-".join(items)) <= max_length:
            break
        else:
            items[i] = trimmed_items[i]

    name = "-".join(items)
    if len(name) > max_length:
        raise Exception(
            "AWS resource name {} exceeds maximum length of {}".format(name, max_length)
        )
    invalid_chars = re.compile("[^a-zA-Z0-9-]|_")
    name = re.sub(invalid_chars, "-", name)
    return name


def generate_ec2_resource_names(name):
    sam_template_name = generate_aws_compatible_string(f"{name}-template")
    deployment_stack_name = generate_aws_compatible_string(f"{name}-stack")
    s3_bucket_name = generate_aws_compatible_string(f"{name}-storage")
    repo_name = generate_aws_compatible_string(f"{name}-repo")
    elb_name = generate_aws_compatible_string(f"{name}-elb", max_length=32)

    return sam_template_name, deployment_stack_name, s3_bucket_name, repo_name, elb_name


def generate_docker_image_tag(registry_uri, bento_name, bento_version):
    image_tag = f"{bento_name}-{bento_version}".lower()
    return f"{registry_uri}:{image_tag}"


def generate_user_data_script(
    registry, image_tag, region, env_vars={}, enable_gpus=False, port=5000
):
    """
    Create init script for EC2 containers to download docker image,
    and run container on startup.
    args:
        registry: ECR registry domain
        tag: bento tag
        region: AWS region
        env_var: dict of environment variable to set in the instance
    """

    env_vars_strings = []
    env_vars_string = "--env {var}={value}"

    for var, value in env_vars.items():
        env_vars_strings.append(env_vars_string.format(var=var, value=value))

    if enable_gpus is True:
        gpu_flag = "--gpus all"
    else:
        gpu_flag = ""

    base_format = EC2_USER_INIT_SCRIPT.format(
        registry=registry,
        tag=image_tag,
        region=region,
        bentoservice_port=port,
        env_vars=" ".join(env_vars_strings),
        gpu_flag=gpu_flag,
    )
    encoded = base64.b64encode(base_format.encode("ascii")).decode("ascii")
    return encoded


def generate_cloudformation_template_file(
    project_dir,
    user_data,
    s3_bucket_name,
    sam_template_name,
    elb_name,
    ami_id,
    instance_type,
    autoscaling_min_size,
    autoscaling_desired_capacity,
    autoscaling_max_size,
    health_check_interval_seconds,
    health_check_path,
    health_check_port,
    health_check_timeout_seconds,
    healthy_threshold_count,
):
    """
    Create and save cloudformation template for deployment
    args:
        project_dir: path to save template file
        user_data: base64 encoded user data for cloud-init script
        s3_bucket_name: AWS S3 bucket name
        sam_template_name: template name to save
        ami_id: ami id for EC2 container to use
        instance_type: EC2 instance type
        autocaling_min_size: autoscaling group minimum size
        autocaling_desired_capacity: autoscaling group desired size
        autocaling_min_size: autoscaling group maximum size


    NOTE: SSH ACCESS TO INSTANCE MAY NOT BE REQUIRED
    """

    template_file_path = os.path.join(project_dir, sam_template_name)
    with open(template_file_path, "a") as f:
        f.write(
            EC2_CLOUDFORMATION_TEMPLATE.format(
                ami_id=ami_id,
                template_name=sam_template_name,
                instance_type=instance_type,
                user_data=user_data,
                elb_name=elb_name,
                autoscaling_min_size=autoscaling_min_size,
                autoscaling_desired_capacity=autoscaling_desired_capacity,
                autoscaling_max_size=autoscaling_max_size,
                s3_bucket_name=s3_bucket_name,
                target_health_check_interval_seconds=health_check_interval_seconds,
                target_health_check_path=health_check_path,
                target_health_check_port=health_check_port,
                target_health_check_timeout_seconds=health_check_timeout_seconds,
                target_health_check_threshold_count=healthy_threshold_count,
            )
        )
    return template_file_path
