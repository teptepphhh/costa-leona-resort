#!/usr/bin/env bash
# Costa Leona - schedule the two automations with EventBridge -> SSM Run Command. Run in CloudShell as SAM10-AdminRole.
# Only instances tagged Project=SAM10 and Role=web are targeted (the instance owned by other coursework is never touched).
set -euo pipefail
export AWS_DEFAULT_REGION=ap-southeast-1
R=$AWS_DEFAULT_REGION
ACCT=$(aws sts get-caller-identity --query Account --output text)
RULE_ROLE=costaleona-events-ssm-role

cat > /tmp/evtrust.json <<EOF
{"Version":"2012-10-17","Statement":[{"Effect":"Allow","Principal":{"Service":"events.amazonaws.com"},"Action":"sts:AssumeRole"}]}
EOF
aws iam create-role --role-name $RULE_ROLE --assume-role-policy-document file:///tmp/evtrust.json --tags Key=Project,Value=SAM10 >/dev/null 2>&1 || echo "role exists"
cat > /tmp/evpolicy.json <<EOF
{"Version":"2012-10-17","Statement":[
 {"Effect":"Allow","Action":"ssm:SendCommand","Resource":"arn:aws:ssm:$R::document/AWS-RunShellScript"},
 {"Effect":"Allow","Action":"ssm:SendCommand","Resource":"arn:aws:ec2:$R:$ACCT:instance/*","Condition":{"StringEquals":{"ec2:ResourceTag/Project":"SAM10","ec2:ResourceTag/Role":"web"}}}]}
EOF
aws iam put-role-policy --role-name $RULE_ROLE --policy-name send-command --policy-document file:///tmp/evpolicy.json
sleep 8

mk() {  # rule-name schedule script
  aws events put-rule --name "$1" --schedule-expression "$2" --state ENABLED --description "Costa Leona automation: $3" --tags Key=Project,Value=SAM10 >/dev/null
  cat > /tmp/target-$1.json <<EOF
[{"Id":"run-$1","Arn":"arn:aws:ssm:$R::document/AWS-RunShellScript","RoleArn":"arn:aws:iam::$ACCT:role/$RULE_ROLE",
  "Input":"{\"commands\":[\"bash /opt/leona/automation/$3\"]}",
  "RunCommandParameters":{"RunCommandTargets":[{"Key":"tag:Role","Values":["web"]},{"Key":"tag:Project","Values":["SAM10"]}]}}]
EOF
  aws events put-targets --rule "$1" --targets file:///tmp/target-$1.json >/dev/null
  echo "scheduled $1 ($2) -> $3"
}
mk costaleona-backup-hourly "rate(1 hour)" backup.sh
mk costaleona-smoketest-hourly "rate(1 hour)" smoketest.sh
aws events list-rules --name-prefix costaleona- --query 'Rules[].[Name,ScheduleExpression,State]' --output table
