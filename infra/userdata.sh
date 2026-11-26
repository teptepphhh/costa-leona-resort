#!/bin/bash
# EC2 first-boot script (user data). Installs Docker, pulls the repo and starts the stack.
exec > >(tee -a /var/log/leona-userdata.log) 2>&1
set -x
export AWS_DEFAULT_REGION=ap-southeast-1
dnf install -y docker git jq amazon-cloudwatch-agent
systemctl enable --now docker
mkdir -p /usr/local/lib/docker/cli-plugins
curl -fsSL https://github.com/docker/compose/releases/download/v2.29.7/docker-compose-linux-x86_64 -o /usr/local/lib/docker/cli-plugins/docker-compose
chmod +x /usr/local/lib/docker/cli-plugins/docker-compose
# 2 GB swap so a memory spike does not kill the database
fallocate -l 2G /swapfile && chmod 600 /swapfile && mkswap /swapfile && swapon /swapfile
echo '/swapfile none swap sw 0 0' >> /etc/fstab
REPO=$(aws ssm get-parameter --name /costaleona/repo_url --query Parameter.Value --output text)
git clone "$REPO" /opt/leona
bash /opt/leona/infra/start.sh
