#!/bin/bash
# Create the demo guest-desk user on the instance. The password is read from Parameter Store
# (SecureString /costaleona/demo_user_password), so it is never typed into a command line or the repo.
set -euo pipefail
export AWS_DEFAULT_REGION=ap-southeast-1
PW=$(aws ssm get-parameter --name /costaleona/demo_user_password --with-decryption --query Parameter.Value --output text)
cd /opt/leona
docker exec costa-leona-web npm run create-user -- admin@costaleona.example "Resort Admin" resortadmin "$PW" --email-verified=true
echo "demo user created $(date -u +%FT%TZ)"
