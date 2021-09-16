import sys
import json
import boto3
import os
import argparse

from rich.pretty import pprint

from ec2 import generate_ec2_resource_names
from utils import get_configuration_value


def get_instance_public_ip(instance_id, region):
    ec2_client = boto3.client("ec2", region)
    response = ec2_client.describe_instances(InstanceIds=[instance_id])
    all_instances = response["Reservations"][0]["Instances"]
    if all_instances:
        if "PublicIpAddress" in all_instances[0]:
            return all_instances[0]["PublicIpAddress"]
    return ""


def get_instance_ip_from_scaling_group(autoscaling_group_names, region):
    asg_client = boto3.client("autoscaling", region)
    response = asg_client.describe_auto_scaling_groups(
        AutoScalingGroupNames=autoscaling_group_names
    )
    all_autoscaling_group_info = response["AutoScalingGroups"]

    all_instances = []
    if all_autoscaling_group_info:
        for group in all_autoscaling_group_info:
            for instance in group["Instances"]:
                endpoint = get_instance_public_ip(instance["InstanceId"], region)
                all_instances.append(
                    {
                        "instance_id": instance["InstanceId"],
                        "endpoint": endpoint,
                        "state": instance["LifecycleState"],
                        "health_status": instance["HealthStatus"],
                    }
                )

    return all_instances


def get_endpoints_from_instance_address(instances):
    all_endpoints = []
    for instance in instances:
        if instance["state"] == "InService":
            all_endpoints.append(
                "{ep}:{port}/".format(ep=instance["endpoint"], port=5000)
            )

    return all_endpoints


def describe(deployment_name, config_json):
    ec2_config = get_configuration_value(config_json)
    _, stack_name, _, _ = generate_ec2_resource_names(deployment_name)

    cf_client = boto3.client("cloudformation", ec2_config["region"])
    result = cf_client.describe_stacks(StackName=stack_name)
    stack_info = result.get("Stacks")
    outputs = stack_info[0].get("Outputs")
    info_json = {}
    outputs = {o["OutputKey"]: o["OutputValue"] for o in outputs}
    if "AutoScalingGroup" in outputs:
        info_json["InstanceDetails"] = get_instance_ip_from_scaling_group(
            [outputs["AutoScalingGroup"]], ec2_config["region"]
        )
        info_json["Endpoints"] = get_endpoints_from_instance_address(
            info_json["InstanceDetails"]
        )
    if "TargetGroup" in outputs:
        info_json["TargetGroup"] = outputs["TargetGroup"]
    if "Url" in outputs:
        info_json["Url"] = outputs["Url"]

    return info_json


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Describe the bundle deployed on EC2",
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

    info_json = describe(args.deployment_name, args.config_json)
    pprint(info_json)
