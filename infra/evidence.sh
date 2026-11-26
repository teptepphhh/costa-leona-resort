#!/usr/bin/env bash
# Prints command-line evidence (cannot be edited by hand). Never prints secret values.
# Usage: bash infra/evidence.sh 1   (backup/S3)   2 (security/IAM/SSM)   3 (compute/network)
export AWS_DEFAULT_REGION=ap-southeast-1
ACCT=$(aws sts get-caller-identity --query Account --output text)
B=costaleona-${ACCT}-content
case "${1:-1}" in
1)
  echo "# S3 versioning on content bucket"; aws s3api get-bucket-versioning --bucket "$B"
  echo "# S3 encryption + public access block"; aws s3api get-bucket-encryption --bucket "$B" --query 'ServerSideEncryptionConfiguration.Rules[0].ApplyServerSideEncryptionByDefault' ; aws s3api get-public-access-block --bucket "$B" --query PublicAccessBlockConfiguration
  echo "# S3 lifecycle (backups kept 14 days)"; aws s3api get-bucket-lifecycle-configuration --bucket "$B" --query 'Rules[].[ID,Expiration.Days]' --output text
  echo "# Knowledge base objects"; aws s3 ls "s3://$B/knowledge/"
  echo "# Latest backups"; aws s3 ls "s3://$B/backups/mongo/" | tail -5
  ;;
2)
  echo "# IAM users and MFA"; aws iam list-users --query 'Users[].UserName' --output text
  for u in $(aws iam list-users --query 'Users[].UserName' --output text); do echo "MFA for $u:"; aws iam list-mfa-devices --user-name "$u" --query 'MFADevices[].SerialNumber' --output text; done
  echo "# Access keys per user (none expected)"; for u in $(aws iam list-users --query 'Users[].UserName' --output text); do echo "$u: $(aws iam list-access-keys --user-name "$u" --query 'AccessKeyMetadata[].AccessKeyId' --output text)"; done
  echo "# Parameter Store (names and types only)"; aws ssm describe-parameters --parameter-filters Key=Path,Values=/costaleona --query 'Parameters[].[Name,Type]' --output table
  echo "# CloudTrail"; aws cloudtrail get-trail-status --name costaleona-trail --query '{IsLogging:IsLogging}' --output text
  echo "# GuardDuty"; aws guardduty get-detector --detector-id "$(aws guardduty list-detectors --query 'DetectorIds[0]' --output text)" --query Status --output text
  ;;
3)
  echo "# Instance"; aws ec2 describe-instances --filters Name=tag:Project,Values=SAM10 --query 'Reservations[].Instances[].[InstanceId,InstanceType,State.Name,MetadataOptions.HttpTokens,Placement.AvailabilityZone]' --output table
  echo "# Volumes encrypted"; aws ec2 describe-volumes --filters Name=tag:Project,Values=SAM10 --query 'Volumes[].[VolumeId,Size,Encrypted]' --output table
  echo "# Security group rules (no SSH, no 0.0.0.0/0)"; aws ec2 describe-security-groups --filters Name=group-name,Values=costaleona-web --query 'SecurityGroups[].IpPermissions[]' --output json
  echo "# Log groups and retention"; aws logs describe-log-groups --log-group-name-prefix /costaleona --query 'logGroups[].[logGroupName,retentionInDays]' --output table
  echo "# Schedules"; aws events list-rules --name-prefix costaleona- --query 'Rules[].[Name,ScheduleExpression,State]' --output table
  ;;
esac
