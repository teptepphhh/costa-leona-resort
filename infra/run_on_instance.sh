#!/usr/bin/env bash
# Run a repo script on the web instance via SSM Run Command (no SSH) and print its output.
#   bash infra/run_on_instance.sh incident/01_cause_fault.sh
set -uo pipefail
export AWS_DEFAULT_REGION=ap-southeast-1
SCRIPT="${1:?usage: run_on_instance.sh <path-in-repo>}"
IID=$(aws ec2 describe-instances --filters Name=tag:Name,Values=costaleona-web Name=instance-state-name,Values=running --query 'Reservations[0].Instances[0].InstanceId' --output text)
CID=$(aws ssm send-command --instance-ids "$IID" --document-name AWS-RunShellScript --comment "run $SCRIPT" \
  --parameters "commands=[\"cd /opt/leona && git pull -q && bash $SCRIPT\"]" --query Command.CommandId --output text)
echo "command $CID on $IID at $(date -u +%FT%TZ)"
for i in $(seq 1 60); do
  S=$(aws ssm get-command-invocation --command-id "$CID" --instance-id "$IID" --query Status --output text 2>/dev/null)
  echo "$(date -u +%T)Z $S"
  case "$S" in Success|Failed|Cancelled|TimedOut) break;; esac
  sleep 10
done
aws ssm get-command-invocation --command-id "$CID" --instance-id "$IID" --query StandardOutputContent --output text
aws ssm get-command-invocation --command-id "$CID" --instance-id "$IID" --query StandardErrorContent --output text | tail -5
