#!/bin/bash
# Render .env from Parameter Store and (re)start the stack. Also used to deploy updates:
#   cd /opt/leona && git pull && bash infra/start.sh
# Secrets are fetched at runtime and written only to /opt/leona/.env (mode 600, git-ignored).
# The Gemini key is NOT written anywhere: the gateway reads it from SSM itself.
set -euo pipefail
export AWS_DEFAULT_REGION=ap-southeast-1
cd /opt/leona
P=/costaleona
get() { aws ssm get-parameter --name "$P/$1" --with-decryption --query Parameter.Value --output text; }

DOMAIN=""
for i in $(seq 1 90); do
  DOMAIN=$(get domain 2>/dev/null || true)
  [[ "$DOMAIN" =~ ^https://[a-z0-9-]+\.[a-z0-9.-]+$ ]] && break
  echo "waiting for $P/domain ($i)"; sleep 20
done
[[ "$DOMAIN" =~ ^https://[a-z0-9-]+\.[a-z0-9.-]+$ ]] || { echo "no valid domain parameter"; exit 1; }

umask 077
cat > .env <<EOF
APP_TITLE=Costa Leona Resort
CUSTOM_FOOTER=Costa Leona Resort - fictional demo. Leona is an AI assistant: please confirm important details with the front desk.
HELP_AND_FAQ_URL=$DOMAIN
DOMAIN_CLIENT=$DOMAIN
DOMAIN_SERVER=$DOMAIN
PORT=3080
HOST_PORT=80
ENDPOINTS=custom
SEARCH=false
ALLOW_REGISTRATION=${ALLOW_REGISTRATION:-false}
ALLOW_SOCIAL_LOGIN=false
ALLOW_EMAIL_LOGIN=true
SCHEDULES_SINGLE_PROCESS=true
CREDS_KEY=$(get creds_key)
CREDS_IV=$(get creds_iv)
JWT_SECRET=$(get jwt_secret)
JWT_REFRESH_SECRET=$(get jwt_refresh_secret)
LEONA_GATEWAY_TOKEN=$(get gateway_token)
GATEWAY_TOKEN_SSM_PARAM=$P/gateway_token
GEMINI_KEY_SSM_PARAM=$P/gemini_api_key
KNOWLEDGE_BUCKET=$(get bucket)
CW_METRICS=1
AWS_REGION=ap-southeast-1
GEMINI_MODEL=gemini-3.5-flash-lite
GEMINI_FALLBACK_MODEL=gemini-3.5-flash
APP_VERSION=$(git describe --tags --always 2>/dev/null || echo 1.0.0)
EOF

mkdir -p logs/gateway
touch /var/log/leona-automation.log
docker compose -f compose.yaml -f compose.aws.yaml up -d --build

# Prevention for the disk-full incident of 2026-11-26: rotate the application request log (see runbook).
cat > /etc/logrotate.d/leona <<'LR'
/opt/leona/logs/gateway/requests.log {
    hourly
    maxsize 100M
    rotate 3
    compress
    delaycompress
    copytruncate
    missingok
    notifempty
}
LR
mkdir -p /etc/systemd/system/logrotate.timer.d
printf '[Timer]
OnCalendar=
OnCalendar=hourly
' > /etc/systemd/system/logrotate.timer.d/hourly.conf
systemctl daemon-reload && systemctl enable --now logrotate.timer

cp infra/cwagent.json /opt/aws/amazon-cloudwatch-agent/etc/amazon-cloudwatch-agent.json
/opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent-ctl -a fetch-config -m ec2 -c file:/opt/aws/amazon-cloudwatch-agent/etc/amazon-cloudwatch-agent.json -s
echo "start.sh finished $(date -u +%FT%TZ)"
