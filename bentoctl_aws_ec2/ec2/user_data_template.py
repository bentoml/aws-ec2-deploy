EC2_USER_INIT_SCRIPT = """MIME-Version: 1.0
Content-Type: multipart/mixed; boundary=\"==MYBOUNDARY==\"

--==MYBOUNDARY==
Content-Type: text/cloud-config; charset=\"us-ascii\"

runcmd:

- sudo yum update -y
- sudo amazon-linux-extras install docker -y
- sudo service docker start
- sudo usermod -a -G docker ec2-user
- curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
- unzip awscliv2.zip
- sudo ./aws/install
- ln -s /usr/bin/aws aws
- aws ecr get-login-password --region {region}|docker login --username AWS --password-stdin {registry}
- docker pull {tag}
- docker run -p {bentoservice_port}:{bentoservice_port} {gpu_flag} {env_vars} {tag}

--==MYBOUNDARY==--
"""  # noqa: E501
