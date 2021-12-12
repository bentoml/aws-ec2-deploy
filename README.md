<div align="center">
    <h1> AWS EC2 Operator </h1>
    <p>
        <img src="https://user-images.githubusercontent.com/5261489/144035885-7aad0b01-f8c7-41ea-8054-203c2d7eb9ad.png"/>
    </p>
</div>

AWS EC2 is a great choice for deploying containerized and load balanced services in the cloud.
Its ability to autoscale and automated health checking features make it attractive to
users who want to reduce cost and want to horizontally scale base on traffic.

<!--ts-->

## Table of Contents

   * [Prerequisites](#prerequisites)
   * [Quickstart with bentoctl](#quickstart-with-bentoctl)
   * [Quickstart with scripts](#quickstart-with-scripts)
   * [Configuration options](#configuration-options)
   * [Deployment operations](#deployment-operations)
      * [Create a deployment](#create-a-deployment)
      * [Update a deployment](#update-a-deployment)
      * [Get deployment's status and information](#get-deployments-status-and-information)
      * [Delete deployment](#delete-deployment)

<!-- Added by: jjmachan, at: Saturday 11 December 2021 10:39:25 AM IST -->

<!--te-->

## Prerequisites

- An active AWS account configured on the machine with AWS CLI installed and configured
    - Install instruction: https://docs.aws.amazon.com/cli/latest/userguide/cli-chap-install.html
    - Configure AWS account instruction: https://docs.aws.amazon.com/cli/latest/userguide/cli-chap-configure.html
- Latest version of `aws-cli > 2.0` and `sam-cli > 1.0`.
- Docker is installed and running on the machine.
    - Install instruction: https://docs.docker.com/install

## Quickstart with bentoctl

Bentoctl is a CLI tool that you can use to deploy bentos to EC2. It helps in configuring and managing your deployments super easy. 

1. Install bentoctl via pip
```
$ pip install bentoctl
```

2. Add AWS EC2 operator
```
$ bentoctl operator add aws-ec2
```

3. Generate deployment_config.yaml file for your deployment. The `bentoctl generate` command can be used to interactively create the `deployment_config.yaml` file which is used to configure the deployment.
```
$ bentoctl generate

Bentoctl Interactive Deployment Spec Builder

Welcome! You are now in interactive mode.

This mode will help you setup the deployment_spec.yaml file required for
deployment. Fill out the appropriate values for the fields.

(deployment spec will be saved to: ./deployment_spec.yaml)

api_version: v1
metadata:
    name: test
    operator: aws-ec2
spec:
    bento: .
    region: us-west-1
    instance_type: t2.micro
    ami_id: /aws/service/ami-amazon-linux-latest/amzn2-ami-hvm-x86_64-gp2
    enable_gpus: False
    ec2_auto_scale:
        min_size: 1
        desired_capacity: 1
        max_size: 1
    elastic_load_balancing:
        health_check_interval_seconds: 5
        health_check_path: /healthz
        health_check_port: 5000
        health_check_timeout_seconds: 3
        healthy_threshold_count: 2
    environment_variables:
filename for deployment_spec [deployment_spec.yaml]:
deployment spec file exists! Should I override? [Y/n]: y
deployment spec generated to: deployment_spec.yaml
```

4. Deploy to EC2
```
$ bentoctl deploy deployment_config.yaml --describe-deployment
```

6. Check endpoint. We will try and test the endpoint The url for the endpoint given in the output of the describe command or you can also check the API Gateway through the AWS console.

    ```bash
    $ curl -i \
      --header "Content-Type: application/json" \
      --request POST \
      --data '[[5.1, 3.5, 1.4, 0.2]]' \
      https://ps6f0sizt8.execute-api.us-west-2.amazonaws.com/predict

    # Sample output
    HTTP/1.1 200 OK
    Content-Type: application/json
    Content-Length: 3
    Connection: keep-alive
    Date: Tue, 21 Jan 2020 22:43:17 GMT
    x-amzn-RequestId: f49d29ed-c09c-4870-b362-4cf493556cf4
    x-amz-apigw-id: GrC0AEHYPHcF3aA=
    X-Amzn-Trace-Id: Root=1-5e277e7f-e9c0e4c0796bc6f4c36af98c;Sampled=0
    X-Cache: Miss from cloudfront
    Via: 1.1 bb248e7fabd9781d3ed921f068507334.cloudfront.net (CloudFront)
    X-Amz-Cf-Pop: SFO5-C1
    X-Amz-Cf-Id: HZzIJUcEUL8aBI0KcmG35rsG-71KSOcLUNmuYR4wdRb6MZupv9IOpA==

    [0]%

7. Delete deployment
```
$ bentoctl delete deployment_config.yaml
```

## Quickstart with scripts

You can also use this operator directly with the scripts provided. 

1. Build and save Bento Bundle from [BentoML quick start guide](https://github.com/bentoml/BentoML/blob/master/guides/quick-start/bentoml-quick-start-guide.ipynb)

2. Copy and change the [sample config file](ec2_config.json) given and change it according to your deployment specifications. Check out the [config section](#configuration-options) to find the different options available.

3. Install required python packages 
   `$ pip install -r requirements.txt`

3. Create EC2 deployment with the deployment tool. 
    
    Run deploy script in the command line:

    ```bash
    $ BENTO_BUNDLE_PATH=$(bentoml get IrisClassifier:latest --print-location -q)
    $ ./deploy $BENTO_BUNDLE_PATH my-first-ec2-deployment ec2_config.json
    ```


    Get EC2 deployment information and status

    ```bash
    $ ./describe my-first-ec2-deployment

    # Sample output
    {
      "InstanceDetails": [
        {
          "instance_id": "i-03ff2d1b9b717a109",
          "endpoint": "3.101.38.18",
          "state": "InService",
          "health_status": "Healthy"
        }
      ],
      "Endpoints": [
        "3.101.38.18:5000/"
      ],
      "S3Bucket": "my-ec2-deployment-storage",
      "TargetGroup": "arn:aws:elasticloadbalancing:us-west-1:192023623294:targetgroup/my-ec-Targe-3G36XKKIJZV9/d773b029690c84d3",
      "Url": "http://my-ec2-deployment-elb-2078733703.us-west-1.elb.amazonaws.com"
    }
    ```

4. Make sample request against deployed service. The url for the endpoint given in the output of the describe command or you can also check the API Gateway through the AWS console.

    ```bash
    $ curl -i \
      --header "Content-Type: application/json" \
      --request POST \
      --data '[[5.1, 3.5, 1.4, 0.2]]' \
      https://ps6f0sizt8.execute-api.us-west-2.amazonaws.com/predict

    # Sample output
    HTTP/1.1 200 OK
    Content-Type: application/json
    Content-Length: 3
    Connection: keep-alive
    Date: Tue, 21 Jan 2020 22:43:17 GMT
    x-amzn-RequestId: f49d29ed-c09c-4870-b362-4cf493556cf4
    x-amz-apigw-id: GrC0AEHYPHcF3aA=
    X-Amzn-Trace-Id: Root=1-5e277e7f-e9c0e4c0796bc6f4c36af98c;Sampled=0
    X-Cache: Miss from cloudfront
    Via: 1.1 bb248e7fabd9781d3ed921f068507334.cloudfront.net (CloudFront)
    X-Amz-Cf-Pop: SFO5-C1
    X-Amz-Cf-Id: HZzIJUcEUL8aBI0KcmG35rsG-71KSOcLUNmuYR4wdRb6MZupv9IOpA==

    [0]%
    ```

5. Delete EC2 deployment

    ```bash
    $ ./delete my-first-ec2-deployment
    ```

## Configuration options

* `region`: AWS region for EC2 deployment
* `instance_type`: Instance type for the EC2 deployment. See https://aws.amazon.com/ec2/instance-types/ for more info.
* `ami_id`: The Amazon machine image (AMI) used for launching EC2 instance. The default is `/aws/service/ami-amazon-linux-latest/amzn2-ami-hvm-x86_64-gp2`. See https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/AMIs.html for more information.
* `enable_gpus`: (Optional) To enable access to the GPUs if you're using GPU-accelerated instance_types.
* `ec2_auto_scale`:
  * `min_size`:  The minimum number of instances for the auto scale group.
  * `desired_capacity`: The desired capacity for the auto scale group. Auto Scaling group will start by launching as many instances as are specified for desired capacity.
  * `max_size`: The maximum number of instances for the auto scale group
* `elastic_load_balancing`:
  * `health_check_interval_seconds`: The approximate interval, in seconds, between health checks of an individual instance. Valid Range: Minimum value of 5. Maximum value of 300.
  * `health_check_path.`: The URL path for health check. Default is `/healthz`
  * `health_check_port`: Health check port. Default is `5000`
  * `health_check_timeout_seconds`: The amount of time, in seconds, during which no response means a failed health check.
  * `healthy_threshold_count`: The number of consecutive health checks successes required before moving the instance to the Healthy state. Valid Range: Minimum value of 2. Maximum value of 10.
* `environment_variables`: This takes a list of dicts with `name` and `value` keys for ENVAR name and ENVAR value repsectively. They are passed into docker as environment variables. You can also use this to pass bentoml specific environment variable use this. eg `environment_variables: [{'name': 'BENTOML_MB_MAX_BATCH_SIZE': 'value': '300'}]`


## Deployment operations

### Create a deployment

Use command line

```bash
python deploy.py <Bento_bundle_path> <Deployment_name> <Config_JSON default is ./ec2_config.json>
```

Example:

```bash
MY_BUNDLE_PATH=${bentoml get IrisClassifier:latest --print-location -q)
python deploy.py $MY_BUNDLE_PATH my_first_deployment ec2_config.json
```

Use Python API

```python
from bentoctl_aws_ec2 import deploy

deploy(BENTO_BUNDLE_PATH, DEPLOYMENT_NAME, CONFIG_JSON)
```



### Update a deployment

Use command line

```bash
python update.py <Bento_bundle_path> <Deployment_name> <Config_JSON>
```

Use Python API

```python
from bentoctl_aws_ec2 import update
update(BENTO_BUNDLE_PATH, DEPLOYMENT_NAME, CONFIG_JSON)
```

### Get deployment's status and information

Use command line

```bash
python describe.py <Deployment_name> <Config_JSON>
```

Use Python API

```python
from bentoctl_aws_ec2 import describe
describe(DEPLOYMENT_NAME, CONFIG_JSON)
```

### Delete deployment

Use command line

```bash
python delete.py <Deployment_name> <Config_JSON>
```

Use Python API

```python
from  bentoctl_aws_ec2 import delete
delete(DEPLOYMENT_NAME, CONFIG_JSON)
```
