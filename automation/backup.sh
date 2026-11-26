#!/bin/bash
# Automation 1 - scheduled MongoDB backup to S3 (invoked by EventBridge -> SSM Run Command, hourly).
# Writes one timestamped log line per run to /var/log/leona-automation.log (shipped to CloudWatch Logs).
set -uo pipefail
export AWS_DEFAULT_REGION=ap-southeast-1
LOG=/var/log/leona-automation.log
log() { echo "$(date -u +%FT%TZ) backup $*" | tee -a "$LOG"; }
BUCKET=$(aws ssm get-parameter --name /costaleona/bucket --query Parameter.Value --output text)
KEY="backups/mongo/CostaLeona-$(date -u +%Y%m%dT%H%M%SZ).archive.gz"
if docker exec costa-leona-db mongodump --db CostaLeona --archive --gzip | aws s3 cp - "s3://$BUCKET/$KEY" --only-show-errors; then
  SIZE=$(aws s3api head-object --bucket "$BUCKET" --key "$KEY" --query ContentLength --output text)
  log "OK s3://$BUCKET/$KEY bytes=$SIZE"
else
  log "FAILED s3://$BUCKET/$KEY"
  exit 1
fi
