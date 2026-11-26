#!/usr/bin/env bash
# Notification-path test for the alarms that have not fired for real. It sets each alarm to ALARM with
# set-alarm-state (a labelled test, NOT a real fault); CloudWatch e-mails the operator through SNS, then each alarm
# returns to its true state at its next evaluation and sends the OK / state message.
# Run in CloudShell as SAM10-AdminRole.
set -euo pipefail
export AWS_DEFAULT_REGION=ap-southeast-1
for a in cpu-high status-check-failed memory-high response-slow answers-failed empty-answers passrate-low; do
  aws cloudwatch set-alarm-state --alarm-name "costaleona-$a" --state-value ALARM \
    --state-reason "PLANNED NOTIFICATION TEST (set-alarm-state), not a real fault - $(date -u +%FT%TZ)"
  echo "test sent for costaleona-$a at $(date -u +%T)Z"
done
