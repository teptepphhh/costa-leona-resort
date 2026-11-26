#!/usr/bin/env bash
# Restore test (content): delete a knowledge file from S3, then bring it back from its previous version.
# Run in CloudShell as SAM10-AdminRole (the instance role cannot delete, by design).
set -euo pipefail
export AWS_DEFAULT_REGION=ap-southeast-1
ACCT=$(aws sts get-caller-identity --query Account --output text)
B=costaleona-${ACCT}-content
K=knowledge/05_house_rules.md
say() { echo "[$(date -u +%FT%TZ)] $*"; }
aws s3 cp "s3://$B/$K" /tmp/before.md --only-show-errors
say "BEFORE: $(sha256sum /tmp/before.md | cut -c1-16)  objects in knowledge/: $(aws s3 ls "s3://$B/knowledge/" | wc -l)"
aws s3 rm "s3://$B/$K" >/dev/null
say "DELETED (a delete marker was created): objects in knowledge/ now: $(aws s3 ls "s3://$B/knowledge/" | wc -l)"
VID=$(aws s3api list-object-versions --bucket "$B" --prefix "$K" --query 'DeleteMarkers[?IsLatest==`true`].VersionId' --output text)
aws s3api delete-object --bucket "$B" --key "$K" --version-id "$VID" >/dev/null
say "RESTORED by removing the delete marker: objects in knowledge/: $(aws s3 ls "s3://$B/knowledge/" | wc -l)"
aws s3 cp "s3://$B/$K" /tmp/after.md --only-show-errors
say "AFTER:  $(sha256sum /tmp/after.md | cut -c1-16)"
cmp /tmp/before.md /tmp/after.md && say "RESULT PASS - restored file is byte-identical"
