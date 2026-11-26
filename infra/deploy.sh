#!/usr/bin/env bash
# Costa Leona - core AWS deployment. Run in AWS CloudShell (region ap-southeast-1) as the SAM10-AdminRole.
#   ALERT_EMAIL=you@example.com REPO_URL=https://github.com/<user>/<repo>.git bash infra/deploy.sh
# Idempotent: safe to re-run. No secret is stored in this file; the model key is typed in (hidden) once.
set -euo pipefail
export AWS_DEFAULT_REGION=ap-southeast-1
R=$AWS_DEFAULT_REGION
: "${ALERT_EMAIL:?set ALERT_EMAIL}"
: "${REPO_URL:?set REPO_URL}"
ACCT=$(aws sts get-caller-identity --query Account --output text)
P=/costaleona
BUCKET=costaleona-${ACCT}-content
say() { echo; echo "==> $*"; }

say "1/9 S3 bucket (versioned, encrypted, private): $BUCKET"
if ! aws s3api head-bucket --bucket "$BUCKET" 2>/dev/null; then
  aws s3api create-bucket --bucket "$BUCKET" --create-bucket-configuration LocationConstraint=$R >/dev/null
fi
aws s3api put-bucket-versioning --bucket "$BUCKET" --versioning-configuration Status=Enabled
aws s3api put-bucket-encryption --bucket "$BUCKET" --server-side-encryption-configuration '{"Rules":[{"ApplyServerSideEncryptionByDefault":{"SSEAlgorithm":"AES256"}}]}'
aws s3api put-public-access-block --bucket "$BUCKET" --public-access-block-configuration BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true
aws s3api put-bucket-tagging --bucket "$BUCKET" --tagging '{"TagSet":[{"Key":"Project","Value":"SAM10"},{"Key":"Team","Value":"solo"}]}'
aws s3api put-bucket-lifecycle-configuration --bucket "$BUCKET" --lifecycle-configuration '{"Rules":[{"ID":"expire-backups-14d","Status":"Enabled","Filter":{"Prefix":"backups/"},"Expiration":{"Days":14},"NoncurrentVersionExpiration":{"NoncurrentDays":14}},{"ID":"expire-old-versions-30d","Status":"Enabled","Filter":{"Prefix":"knowledge/"},"NoncurrentVersionExpiration":{"NoncurrentDays":30}}]}'
aws s3 sync knowledge "s3://$BUCKET/knowledge/" --delete --only-show-errors

say "2/9 Parameter Store (SecureString secrets, generated here, never in git)"
put_secret() {  # name value
  if aws ssm get-parameter --name "$P/$1" >/dev/null 2>&1; then echo "exists   $P/$1"; else
    aws ssm put-parameter --name "$P/$1" --type SecureString --value "$2" --tags Key=Project,Value=SAM10 >/dev/null && echo "created  $P/$1"; fi
}
put_string() {
  aws ssm put-parameter --name "$P/$1" --type String --value "$2" --overwrite >/dev/null && echo "set      $P/$1"
}
if ! aws ssm get-parameter --name "$P/gemini_api_key" >/dev/null 2>&1; then
  read -rsp "Paste the Gemini API key (input hidden): " GK; echo
  put_secret gemini_api_key "$GK"; unset GK
else echo "exists   $P/gemini_api_key"; fi
put_secret creds_key "$(openssl rand -hex 32)"
put_secret creds_iv "$(openssl rand -hex 16)"
put_secret jwt_secret "$(openssl rand -hex 32)"
put_secret jwt_refresh_secret "$(openssl rand -hex 32)"
put_secret gateway_token "$(openssl rand -hex 24)"
put_string bucket "$BUCKET"
put_string repo_url "$REPO_URL"

say "3/9 SNS alert topic + email subscription ($ALERT_EMAIL)"
TOPIC=$(aws sns create-topic --name costaleona-alerts --tags Key=Project,Value=SAM10 --query TopicArn --output text)
aws sns subscribe --topic-arn "$TOPIC" --protocol email --notification-endpoint "$ALERT_EMAIL" >/dev/null
put_string alert_topic "$TOPIC"
echo "CHECK YOUR INBOX and click 'Confirm subscription'."

say "4/9 IAM role for the instance (least privilege)"
cat > /tmp/ec2trust.json <<EOF
{"Version":"2012-10-17","Statement":[{"Effect":"Allow","Principal":{"Service":"ec2.amazonaws.com"},"Action":"sts:AssumeRole"}]}
EOF
aws iam create-role --role-name costaleona-ec2-role --assume-role-policy-document file:///tmp/ec2trust.json --tags Key=Project,Value=SAM10 >/dev/null 2>&1 || echo "role exists"
aws iam attach-role-policy --role-name costaleona-ec2-role --policy-arn arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore
aws iam attach-role-policy --role-name costaleona-ec2-role --policy-arn arn:aws:iam::aws:policy/CloudWatchAgentServerPolicy
cat > /tmp/ec2policy.json <<EOF
{"Version":"2012-10-17","Statement":[
 {"Effect":"Allow","Action":["s3:GetObject","s3:PutObject","s3:ListBucket","s3:GetBucketLocation"],"Resource":["arn:aws:s3:::$BUCKET","arn:aws:s3:::$BUCKET/*"]},
 {"Effect":"Allow","Action":["ssm:GetParameter","ssm:GetParameters","ssm:GetParametersByPath"],"Resource":"arn:aws:ssm:$R:$ACCT:parameter/costaleona/*"},
 {"Effect":"Allow","Action":"cloudwatch:PutMetricData","Resource":"*","Condition":{"StringEquals":{"cloudwatch:namespace":["CostaLeona","CWAgent"]}}},
 {"Effect":"Allow","Action":"sns:Publish","Resource":"$TOPIC"}]}
EOF
aws iam put-role-policy --role-name costaleona-ec2-role --policy-name costaleona-app --policy-document file:///tmp/ec2policy.json
aws iam create-instance-profile --instance-profile-name costaleona-ec2-profile --tags Key=Project,Value=SAM10 >/dev/null 2>&1 || true
aws iam add-role-to-instance-profile --instance-profile-name costaleona-ec2-profile --role-name costaleona-ec2-role >/dev/null 2>&1 || true

say "5/9 Security group (HTTP only from CloudFront; no SSH - use Session Manager)"
VPC=$(aws ec2 describe-vpcs --filters Name=isDefault,Values=true --query 'Vpcs[0].VpcId' --output text)
SG=$(aws ec2 describe-security-groups --filters Name=group-name,Values=costaleona-web Name=vpc-id,Values="$VPC" --query 'SecurityGroups[0].GroupId' --output text)
if [ "$SG" = "None" ]; then
  SG=$(aws ec2 create-security-group --group-name costaleona-web --description "Costa Leona web: CloudFront only" --vpc-id "$VPC" \
       --tag-specifications 'ResourceType=security-group,Tags=[{Key=Project,Value=SAM10},{Key=Name,Value=costaleona-web}]' --query GroupId --output text)
fi
PL=$(aws ec2 describe-managed-prefix-lists --filters Name=prefix-list-name,Values=com.amazonaws.global.cloudfront.origin-facing --query 'PrefixLists[0].PrefixListId' --output text)
aws ec2 authorize-security-group-ingress --group-id "$SG" --ip-permissions "IpProtocol=tcp,FromPort=80,ToPort=80,PrefixListIds=[{PrefixListId=$PL,Description=CloudFront-only}]" >/dev/null 2>&1 || echo "ingress rule exists"

say "6/9 CloudWatch log groups (retention 14 days)"
for g in librechat gateway mongodb requests system; do
  aws logs create-log-group --log-group-name /costaleona/$g --tags Project=SAM10 2>/dev/null || true
  aws logs put-retention-policy --log-group-name /costaleona/$g --retention-in-days 14
done

say "7/9 EC2 instance (t3.small, encrypted gp3 20 GB, IMDSv2)"
IID=$(aws ec2 describe-instances --filters Name=tag:Name,Values=costaleona-web Name=instance-state-name,Values=pending,running,stopped --query 'Reservations[0].Instances[0].InstanceId' --output text)
if [ "$IID" = "None" ]; then
  sleep 10
  AMI=$(aws ssm get-parameter --name /aws/service/ami-amazon-linux-latest/al2023-ami-kernel-default-x86_64 --query Parameter.Value --output text)
  IID=$(aws ec2 run-instances --image-id "$AMI" --instance-type t3.small --iam-instance-profile Name=costaleona-ec2-profile \
    --security-group-ids "$SG" --metadata-options HttpTokens=required,HttpPutResponseHopLimit=2,HttpEndpoint=enabled \
    --block-device-mappings 'DeviceName=/dev/xvda,Ebs={VolumeSize=20,VolumeType=gp3,Encrypted=true,DeleteOnTermination=true}' \
    --user-data file://infra/userdata.sh \
    --tag-specifications 'ResourceType=instance,Tags=[{Key=Name,Value=costaleona-web},{Key=Project,Value=SAM10},{Key=Role,Value=web},{Key=Team,Value=solo}]' 'ResourceType=volume,Tags=[{Key=Project,Value=SAM10}]' \
    --query 'Instances[0].InstanceId' --output text)
fi
aws ec2 wait instance-running --instance-ids "$IID"
DNS=$(aws ec2 describe-instances --instance-ids "$IID" --query 'Reservations[0].Instances[0].PublicDnsName' --output text)
echo "instance $IID  origin $DNS"

say "8/9 CloudFront (free HTTPS URL on *.cloudfront.net)"
CF=$(aws cloudfront list-distributions --query "DistributionList.Items[?Comment=='costaleona'].[Id,DomainName]" --output text 2>/dev/null || true)
if [ -z "$CF" ]; then
  cat > /tmp/cf.json <<EOF
{"CallerReference":"costaleona-$(date +%s)","Comment":"costaleona","Enabled":true,"PriceClass":"PriceClass_100",
 "Origins":{"Quantity":1,"Items":[{"Id":"ec2-origin","DomainName":"$DNS",
   "CustomOriginConfig":{"HTTPPort":80,"HTTPSPort":443,"OriginProtocolPolicy":"http-only","OriginReadTimeout":60,"OriginKeepaliveTimeout":5}}]},
 "DefaultCacheBehavior":{"TargetOriginId":"ec2-origin","ViewerProtocolPolicy":"redirect-to-https",
   "AllowedMethods":{"Quantity":7,"Items":["GET","HEAD","OPTIONS","PUT","POST","PATCH","DELETE"],"CachedMethods":{"Quantity":2,"Items":["GET","HEAD"]}},
   "CachePolicyId":"4135ea2d-6df8-44a3-9df3-4b5a84be39ad","OriginRequestPolicyId":"216adef6-5c7f-47e4-b989-5492eafa07d3","Compress":true}}
EOF
  CF=$(aws cloudfront create-distribution --distribution-config file:///tmp/cf.json --query '[Distribution.Id,Distribution.DomainName]' --output text)
  aws cloudfront tag-resource --resource "arn:aws:cloudfront::$ACCT:distribution/$(echo "$CF" | cut -f1)" --tags 'Items=[{Key=Project,Value=SAM10}]' || true
fi
CFID=$(echo "$CF" | awk '{print $1}'); CFDOM=$(echo "$CF" | awk '{print $2}')
put_string domain "https://$CFDOM"
put_string cloudfront_id "$CFID"

say "9/9 Done"
echo "Instance:   $IID"
echo "Bucket:     $BUCKET"
echo "Alert topic $TOPIC"
echo "URL (ready in ~10 min, after CloudFront deploys and the instance finishes booting):"
echo "  https://$CFDOM"
echo "Follow the instance boot:  aws ssm start-session --target $IID   (or check /costaleona/* log groups)"
