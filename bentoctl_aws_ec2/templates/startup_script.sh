#!/bin/bash
sudo yum update -y
sudo amazon-linux-extras install docker -y
sudo service docker start
sudo usermod -a -G docker ec2-user
newgrp docker
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install
ln -s /usr/bin/aws aws
aws ecr get-login-password --region {region} |docker login --username AWS --password-stdin {registry_url}
docker pull {image_tag}
docker run -p {SERVICE_PORT}:{BENTOML_PORT} {gpu_flag} {image_tag}
