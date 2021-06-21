import sys
import json
import boto3

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


def describe_deployment(deployment_name, config_json):
    ec2_config = get_configuration_value(config_json)
    _, stack_name, _, _, _ = generate_ec2_resource_names(deployment_name)

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
    if "S3Bucket" in outputs:
        info_json["S3Bucket"] = outputs["S3Bucket"]
    if "TargetGroup" in outputs:
        info_json["TargetGroup"] = outputs["TargetGroup"]
    if "Url" in outputs:
        info_json["Url"] = outputs["Url"]
    print(json.dumps(info_json, indent=2))


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise Exception("Please provide deployment_name and configuration json")
    deployment_name = sys.argv[1]
    config_json = sys.argv[2] if sys.argv[2] else "ec2_config.json"

    describe_deployment(deployment_name, config_json)
