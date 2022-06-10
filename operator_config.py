OPERATOR_SCHEMA = {
    "region": {
        "required": True,
        "type": "string",
        "default": "us-west-1",
        "help_message": "AWS region to which you want to deploy",
    },
    "instance_type": {
        "type": "string",
        "default": "t2.micro",
        "help_message": "Instance type for the EC2 deployment."
        " See https://aws.amazon.com/ec2/instance-types/ for the entire list.",
    },
    "ami_id": {
        "type": "string",
        "default": "ami-0a3277ffce9146b74",
        "help_message": "Amazon Machine Image (AMI) used for the EC2 instance. "
        "Check out https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/AMIs.html "
        "for more information.",
    },
    "enable_gpus": {
        "type": "boolean",
        "default": False,
        "coerce": bool,
        "help_message": "If using GPU-accelerated instance_types then ennable this.",
    },
    "environment_variables": {
        "type": "list",
        "schema": {
            "type": "dict",
            "schema": {
                "name": {
                    "type": "string",
                    "help_message": "Name for environment variable",
                },
                "value": {
                    "type": "string",
                    "help_message": "Value for the environment variables",
                },
            },
        },
    },
}

OPERATOR_NAME = "aws-ec2"
OPERATOR_MODULE = "bentoctl_aws_ec2"
OPERATOR_DEFAULT_TEMPLATE = "terraform"
