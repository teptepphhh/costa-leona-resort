#!/usr/bin/env bash
# Costa Leona - audit trail and threat detection. Run in CloudShell as SAM10-AdminRole.
#  * CloudTrail trail (this region, log-file validation) -> private encrypted S3 bucket
#  * GuardDuty detector (30-day free trial; DISABLE at the end of term - see README "Clean-up")
set -euo pipefail
export AWS_DEFAULT_REGION=ap-southeast-1
R=$AWS_DEFAULT_REGION
ACCT=$(aws sts get-caller-identity --query Account --output text)
TB=costaleona-${ACCT}-trail

echo "==> CloudTrail bucket $TB"
if ! aws s3api head-bucket --bucket "$TB" 2>/dev/null; then
  aws s3api create-bucket --bucket "$TB" --create-bucket-configuration LocationConstraint=$R >/dev/null
fi
aws s3api put-public-access-block --bucket "$TB" --public-access-block-configuration BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true
aws s3api put-bucket-encryption --bucket "$TB" --server-side-encryption-configuration '{"Rules":[{"ApplyServerSideEncryptionByDefault":{"SSEAlgorithm":"AES256"}}]}'
aws s3api put-bucket-tagging --bucket "$TB" --tagging '{"TagSet":[{"Key":"Project","Value":"SAM10"}]}'
aws s3api put-bucket-lifecycle-configuration --bucket "$TB" --lifecycle-configuration '{"Rules":[{"ID":"expire-90d","Status":"Enabled","Filter":{"Prefix":""},"Expiration":{"Days":90}}]}'
cat > /tmp/trailpolicy.json <<EOF
{"Version":"2012-10-17","Statement":[
 {"Sid":"AWSCloudTrailAclCheck","Effect":"Allow","Principal":{"Service":"cloudtrail.amazonaws.com"},"Action":"s3:GetBucketAcl","Resource":"arn:aws:s3:::$TB"},
 {"Sid":"AWSCloudTrailWrite","Effect":"Allow","Principal":{"Service":"cloudtrail.amazonaws.com"},"Action":"s3:PutObject","Resource":"arn:aws:s3:::$TB/AWSLogs/$ACCT/*","Condition":{"StringEquals":{"s3:x-amz-acl":"bucket-owner-full-control"}}}]}
EOF
aws s3api put-bucket-policy --bucket "$TB" --policy file:///tmp/trailpolicy.json

echo "==> CloudTrail trail costaleona-trail"
if ! aws cloudtrail get-trail --name costaleona-trail >/dev/null 2>&1; then
  aws cloudtrail create-trail --name costaleona-trail --s3-bucket-name "$TB" --enable-log-file-validation --no-is-multi-region-trail --tags-list Key=Project,Value=SAM10 >/dev/null
fi
aws cloudtrail start-logging --name costaleona-trail
aws cloudtrail get-trail-status --name costaleona-trail --query '{IsLogging:IsLogging,StartLoggingTime:StartLoggingTime}' --output table

echo "==> GuardDuty"
DET=$(aws guardduty list-detectors --query 'DetectorIds[0]' --output text)
if [ "$DET" = "None" ]; then DET=$(aws guardduty create-detector --enable --tags Project=SAM10 --query DetectorId --output text); fi
aws guardduty get-detector --detector-id "$DET" --query '{Status:Status,Created:CreatedAt}' --output table
echo "done"
