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
        "help_message": "Amazon Machine Image (AMI) used for the EC2 instance. "
        "Choose one from https://console.aws.amazon.com/ec2/home#AMICatalog."
        "Note: Only Amazon Linux AMIs work at the current moment.",
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
