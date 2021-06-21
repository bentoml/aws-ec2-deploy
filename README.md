# BentoML AWS EC2 deployment tool


## Prerequisites

- An active AWS account configured on the machine with AWS CLI installed and configured
    - Install instruction: https://docs.aws.amazon.com/cli/latest/userguide/cli-chap-install.html
    - Configure AWS account instruction: https://docs.aws.amazon.com/cli/latest/userguide/cli-chap-configure.html
- Docker is installed and running on the machine.
    - Install instruction: https://docs.docker.com/install

- Install required python packages
    - `$ pip install -r requirements.txt`


## Deployment operations

### Create a deployment

Use command line
```bash
$ python deploy.py <Bento_bundle_path> <Deployment_name> <Config_JSON default is ec2_config.json>
```

Example:
```bash
$ MY_BUNDLE_PATH=${bentoml get IrisClassifier:latest --print-location -q)
$ python deploy.py $MY_BUNDLE_PATH my_first_deployment ec2_config.json
```

Use Python API
```python
from deploy import deploy_to_ec2

deploy_to_ec2(BENTO_BUNDLE_PATH, DEPLOYMENT_NAME, CONFIG_JSON)
```


#### Available configuration options for EC2 deployments

* `region`: AWS region for EC2 deployment
* `ec2_auto_scale`:
  * `min_size`:  The minimum number of instances for the auto scale group.
  * `desired_capacity`: The desired capacity for the auto scale group. Auto Scaling group will start by launching as many instances as are specified for desired capacity.
  * `max_size`: The maximum number of instances for the auto scale group
* `instance_type`: Instance type for the EC2 deployment. See https://aws.amazon.com/ec2/instance-types/ for more info
* `ami_id`: The Amazon machine image (AMI) used for launching EC2 instance. The default is `/aws/service/ami-amazon-linux-latest/amzn2-ami-hvm-x86_64-gp2`. See https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/AMIs.html for more information.
* `elb`:
  * `health_check_interval_seconds`: The approximate interval, in seconds, between health checks of an individual instance. Valid Range: Minimum value of 5. Maximum value of 300.
  * `health_check_path.`: The URL path for health check. Default is `/healthz`
  * `health_check_port`: Health check port. Default is `5000`
  * `health_check_timeout_seconds`: The amount of time, in seconds, during which no response means a failed health check.
  * `healthy_threshold_count`: The number of consecutive health checks successes required before moving the instance to the Healthy state. Valid Range: Minimum value of 2. Maximum value of 10.


### Update a deployment

Use command line
```bash
$ python update.py <Bento_bundle_path> <Deployment_name> <Config_JSON>
```

Use Python API
```python
from update import update_deployment
update_deployment(BENTO_BUNDLE_PATH, DEPLOYMENT_NAME, CONFIG_JSON)
```

### Describe deployment status and information

Use command line
```bash
$ python describe.py <Deployment_name> <Config_JSON>
```


Use Python API
```python
from describe import describe_deployment
describe_deployment(DEPLOYMENT_NAME, CONFIG_JSON)
```

### Delete deployment

Use command line
```bash
$ python delete.py <Deployment_name> <Config_JSON>
```

Use Python API
```python
from  delete import delete_deployment
delete_deployment(DEPLOYMENT_NAME, CONFIG_JSON)
```
