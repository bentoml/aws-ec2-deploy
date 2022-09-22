<div align="center">
    <h1>AWS EC2 Operator</h1>
</div>

Bentoctl is a CLI tool for deploying your machine-learning models to any cloud platform and serving predictions via REST APIs.
It is built on top of [BentoML: the unified model serving framework](https://github.com/bentoml/bentoml) and makes it easy to bring any BentoML packaged model to production.

This repo contains the AWS EC2 deployment operator. This operator defines the terraform configuration for deploying a bento into an EC2 instance.


> **Note:** This operator is compatible with BentoML version 1.0.0 and above. For older versions, please switch to the branch `pre-v1.0` and follow the instructions in the README.md.


## Table of Contents

   * [Quickstart with bentoctl](#quickstart-with-bentoctl)
   * [Configuration options](#configuration-options)
   * [Troubleshooting](#troubleshooting)


## Quickstart with bentoctl

This quickstart will walk you through deploying a bento into an EC2 instance. Make sure to go through the [prerequisites](#prerequisites) section and follow the instructions to set everything up.

### Prerequisites

1. Bentoml - BentoML version 1.0 and greater. Please follow the [Installation guide](https://docs.bentoml.org/en/latest/quickstart.html#installation).
2. Terraform - [Terraform](https://www.terraform.io/) is a tool for building, configuring, and managing infrastructure. Installation instruction: www.terraform.io/downloads
3. AWS CLI - installed and configured with an AWS account with permission to EC2 and ECR. Please follow the [Installation guide](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html).
4. Docker - Install instruction: [docs.docker.com/install](https://docs.docker.com/install)
5. A built Bento project. For this guide, we will use the Iris classifier bento from the [BentoML quickstart guide](https://docs.bentoml.org/en/latest/quickstart.html#quickstart). You can also use your own Bentos that are available locally.

### Steps

1. Install bentoctl via pip
    ```
    $ pip install bentoctl
    ```

2. Install AWS EC2 operator

    Bentoctl will install the official AWS EC2 operator and its dependencies.

    ```
    $ bentoctl operator install aws-ec2
    ```

3. Initialize deployment with bentoctl

    Follow the interactive guide to initialize the deployment project.

    ```bash
    $ bentoctl init
    
    Bentoctl Interactive Deployment Config Builder

    Welcome! You are now in interactive mode.

    This mode will help you setup the deployment_config.yaml file required for
    deployment. Fill out the appropriate values for the fields.

    (deployment config will be saved to: ./deployment_config.yaml)

    api_version: v1
    name: iris-classifier-ec2
    operator: aws-ec2
    template: terraform
    spec:
        region: ap-south-1
        instance_type: t2.micro
        ami_id: ami-0a3277ffce9146b74
        enable_gpus: False
        environment_variables:
    filename for deployment_config [deployment_config.yaml]:
    deployment config generated to: deployment_config.yaml
    ✨ generated template files.
      - ./main.tf
      - ./bentoctl.tfvars
    ```
    This will also run the `bentoctl generate` command for you and will generate the `main.tf` terraform file, which specifies the resources to be created and the `bentoctl.tfvars` file which contains the values for the variables used in the `main.tf` file.

4. Build and push AWS EC2 compatible docker image to the registry

    Bentoctl will build and push the EC2 compatible docker image to the AWS ECR repository.

    ```bash
    bentoctl build -b iris_classifier:latest -f deployment_config.yaml

    Step 1/22 : FROM bentoml/bento-server:1.0.0a6-python3.8-debian-runtime
     ---> 046bc2e28220
    Step 2/22 : ARG UID=1034
     ---> Using cache
     ---> f44cfa910c52
    Step 3/22 : ARG GID=1034
     ---> Using cache
     ---> e4d5aed007af
    Step 4/22 : RUN groupadd -g $GID -o bentoml && useradd -m -u $UID -g $GID -o -r bentoml
     ---> Using cache
     ---> fa8ddcfa15cf
    ...
    Step 22/22 : CMD ["bentoml", "serve", ".", "--production"]
     ---> Running in 28eccee2f650
     ---> 98bc66e49cd9
    Successfully built 98bc66e49cd9
    Successfully tagged aws-ec2-iris_classifier:kiouq7wmi2gmockr
    🔨 Image build!
    Created the repository iris-classifier-ec2
    The push refers to repository
    [213386773652.dkr.ecr.ap-south-1.amazonaws.com/iris-classifier-ec2]
    kiouq7wmi2gmockr: digest:
    sha256:e1a468e6b9ceeed65b52d0ee2eac9e3cd1a57074eb94db9c263be60e4db98881 size: 3250
    63984d77b4da: Pushed
    2bc5eef20c91: Pushed
    ...
    da0af9cdde98: Layer already exists
    e5baccb54724: Layer already exists
    🚀 Image pushed!
    ✨ generated template files.
      - ./bentoctl.tfvars
      - ./startup_script.sh
    ```
    The iris-classifier service is now built and pushed into the container registry and the required terraform files have been created. Now we can use terraform to perform the deployment.
    
5. Apply Deployment with Terraform

   1. Initialize terraform project. This installs the AWS provider and sets up the terraform folders.
      ```bash
      $ terraform init
      ```

   2. Apply terraform project to create EC2 deployment

        ```bash
        $ terraform apply -var-file=bentoctl.tfvars -auto-approve

        aws_iam_role.ec2_role: Creating...
        aws_security_group.allow_bentoml: Creating...
        aws_security_group.allow_bentoml: Creation complete after 2s [id=sg-01d5baaa464ff58f9]
        aws_iam_role.ec2_role: Creation complete after 3s [id=iris-classifier-ec2-iam]
        aws_iam_instance_profile.ip: Creating...
        aws_iam_instance_profile.ip: Creation complete after 1s [id=iris-classifier-ec2-instance-profile]
        aws_launch_template.lt: Creating...
        aws_launch_template.lt: Creation complete after 0s [id=lt-09d7717f0f1a56001]
        aws_instance.app_server: Creating...
        aws_instance.app_server: Still creating... [10s elapsed]
        aws_instance.app_server: Still creating... [20s elapsed]
        aws_instance.app_server: Still creating... [30s elapsed]
        aws_instance.app_server: Still creating... [40s elapsed]
        aws_instance.app_server: Creation complete after 43s [id=i-0d9767b74865dc0b0]

        Apply complete! Resources: 5 added, 0 changed, 0 destroyed.

        Outputs:

        ec2_instance_status = "running"
        ec2_ip_address = "13.235.76.37"
        ```

6. Test deployed endpoint

    The `iris_classifier` uses the `/classify` endpoint for receiving requests so the full URL for the classifier will be in the form `{EndpointUrl}/classify`.

    ```bash
    URL=$(terraform output -json | jq -r .ec2_ip_address.value)/classify
    curl -i \
      --header "Content-Type: application/json" \
      --request POST \
      --data '[5.1, 3.5, 1.4, 0.2]' \
      $URL

    HTTP/2 200
    date: Thu, 14 Apr 2022 23:02:45 GMT
    content-type: application/json
    content-length: 1
    apigw-requestid: Ql8zbicdSK4EM5g=

    0%
    ```
   
   Please note that the EC2 instance might take some more time to pull the image and setup the bentoml server. You can check if the server is up by pinging the `/livez` endpoint.
   ```bash
   URL=$(terraform output -json | jq -r .ec2_ip_address.value)/livez
   curl $URL
   ```
   If it doesn't start up after a few minutes refer to the [troubleshooting section](#troubleshooting)

7. Delete deployment
    Use the `bentoctl destroy` command to remove the registry and the deployment

    ```bash
    bentoctl destroy -f deployment_config.yaml
    ```
## Configuration options

* `region`: AWS region for deployment
* `instance_type`: Instance type for the EC2 deployment.  See https://aws.amazon.com/ec2/instance-types/ for the entire list.
* `ami_id`: Amazon Machine Image (AMI) used for the EC2 instance. Check out https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/AMIs.html for more information. The list of available AMIs for your region is available at https://console.aws.amazon.com/ec2/home#AMICatalog. AMI Ids are region specific, so make sure you get the AMI Id for the region you want to deploy into.
> Note: Only Amazon Linux AMIs are supported at the current moment. This is the limitation of the startup_script used.
* `ennable_gpus`: If using GPU-accelerated instance_types then ennable this.
* `environment_variables`: List of environment variables that should be passed to the instance.

## Troubleshooting

  To run any troubleshooting we will have to connect to the EC2 instance. The EC2 instance created with terraform has EC2-connect configured by default but you will have to open the SSH port to connect to it.
  
  ### Open SSH port
  
  To open the SSH port, open the `main.tf` that has been generated and add an additional ingress rule into the `aws_security_group` resource named `allow_bentoml`. 
  ```hcl
  resource "aws_security_group" "allow_bentoml" {
    name        = "${var.deployment_name}-bentoml-sg"
    description = "SG for bentoml server"

    ingress {
      description      = "HTTP for bentoml"
      from_port        = 80
      to_port          = 80
      protocol         = "tcp"
      cidr_blocks      = ["0.0.0.0/0"]
      ipv6_cidr_blocks = ["::/0"]
    }

    # add this to open SSH port for the EC2 instance.
    ingress {
      description      = "SSH access for server"
      from_port        = 22
      to_port          = 22
      protocol         = "tcp"
      cidr_blocks      = ["0.0.0.0/0"]
      ipv6_cidr_blocks = ["::/0"]
    }

    egress {
      from_port        = 0
      to_port          = 0
      protocol         = "-1"
      cidr_blocks      = ["0.0.0.0/0"]
      ipv6_cidr_blocks = ["::/0"]
    }
  }
```
  Now you can run terraform apply again to make the changes to the resources.
  ```bash
  terraform apply -var-file=bentoctl.tfvars -auto-approve
  ```
  
  ### Connect to the EC2 instance
  You can connect to an instance using the Amazon EC2 console (browser-based client) by selecting the instance from the console and choosing to connect using EC2 Instance Connect. Instance Connect handles the permissions and provides a successful connection.

To connect to your instance using the browser-based client from the Amazon EC2 console

1. Open the Amazon EC2 console at https://console.aws.amazon.com/ec2/.
2. In the navigation pane, choose Instances.
3. Select the instance and choose Connect.
4. Choose EC2 Instance Connect.
5. Verify the user name and choose Connect to open a terminal window.

For more information check out the [official docs](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ec2-instance-connect-methods.html#ec2-instance-connect-connecting-console)

### Check docker container logs
Once connected, make sure the docker container is running by running
```bash
docker ps
```
This will show all the containers running. Ideally, you should see something like
```
CONTAINER ID   IMAGE                              COMMAND                  CREATED         STATUS        PORTS                                   NAMES
4681b23e0c51   iris_classifier:kiouq7wmi2gmockr   "./env/docker/entryp…"   2 seconds ago   Up 1 second   0.0.0.0:80->3000/tcp, :::80->3000/tcp   bold_kirch
```
To view the logs from the container, run
```
docker logs <NAMES>
```
and it will output the logs from the container.

### Check cloud-init script logs
If the docker container is not running or if the `docker` command is not available in the ec2 instance then it could be an issue with the initialisation script. You can check the logs for the init-script by running
```bash
sudo cat /var/log/cloud-init-output.log
```
