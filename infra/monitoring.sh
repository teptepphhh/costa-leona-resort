#!/usr/bin/env bash
# Costa Leona - CloudWatch alarms (all email via SNS) and dashboard. Run in CloudShell as SAM10-AdminRole.
set -euo pipefail
export AWS_DEFAULT_REGION=ap-southeast-1
R=$AWS_DEFAULT_REGION
IID=$(aws ec2 describe-instances --filters Name=tag:Name,Values=costaleona-web Name=instance-state-name,Values=running,pending --query 'Reservations[0].Instances[0].InstanceId' --output text)
TOPIC=$(aws ssm get-parameter --name /costaleona/alert_topic --query Parameter.Value --output text)
TAGS="Key=Project,Value=SAM10"
echo "instance $IID  topic $TOPIC"

alarm() {  # name desc metric namespace stat period evals threshold operator treat unit-dim
  aws cloudwatch put-metric-alarm --alarm-name "$1" --alarm-description "$2" --metric-name "$3" --namespace "$4" --statistic "$5" \
    --period "$6" --evaluation-periods "$7" --threshold "$8" --comparison-operator "$9" --treat-missing-data "${10}" \
    --dimensions "${11}" --alarm-actions "$TOPIC" --ok-actions "$TOPIC" --tags $TAGS
  echo "alarm  $1"
}
D_EC2="Name=InstanceId,Value=$IID"

# 1 CPU: stuck process or runaway loop
alarm costaleona-cpu-high "CPU above 85% for 10 minutes: check for a stuck process or runaway loop" CPUUtilization AWS/EC2 Average 300 2 85 GreaterThanThreshold missing "$D_EC2"
# 2 Instance status check
alarm costaleona-status-check-failed "EC2 status check failed: look at the instance" StatusCheckFailed AWS/EC2 Maximum 60 1 0 GreaterThanThreshold missing "$D_EC2"
# 3 Disk: a full disk kills the app within minutes, so 85% over 2 minutes (not 1 hour)
alarm costaleona-disk-high "Root disk above 85%: clean up logs or grow the disk (see runbook)" disk_used_percent CWAgent Maximum 60 2 85 GreaterThanThreshold missing "$D_EC2"
# 4 Memory
alarm costaleona-memory-high "Memory above 90% for 5 minutes: containers may be killed" mem_used_percent CWAgent Average 300 1 90 GreaterThanThreshold missing "$D_EC2"
# 5 Slow answers (external AI model typically takes 3-8 s, so 10 s average is the pain line)
aws cloudwatch put-metric-alarm --alarm-name costaleona-response-slow --alarm-description "Average answer time above 10 s for 5 minutes" \
  --metric-name ResponseTimeMs --namespace CostaLeona --statistic Average --period 300 --evaluation-periods 1 --threshold 10000 \
  --comparison-operator GreaterThanThreshold --treat-missing-data notBreaching --alarm-actions "$TOPIC" --ok-actions "$TOPIC" --tags $TAGS
echo "alarm  costaleona-response-slow"
# 6 Empty answers: knowledge base probably missing or unreadable
aws cloudwatch put-metric-alarm --alarm-name costaleona-empty-answers --alarm-description "At least one empty answer in 30 minutes: knowledge base missing or unreadable" \
  --metric-name EmptyAnswer --namespace CostaLeona --statistic Sum --period 1800 --evaluation-periods 1 --threshold 0 \
  --comparison-operator GreaterThanThreshold --treat-missing-data notBreaching --alarm-actions "$TOPIC" --ok-actions "$TOPIC" --tags $TAGS
echo "alarm  costaleona-empty-answers"
# 7 Failed answers above 5% of requests over 15 minutes (metric math, alarms only when there is traffic)
cat > /tmp/failrate.json <<EOF
[{"Id":"rate","Expression":"IF(s+f>0, 100*f/(s+f), 0)","Label":"FailedPercent","ReturnData":true},
 {"Id":"f","MetricStat":{"Metric":{"Namespace":"CostaLeona","MetricName":"AnswersFailed"},"Period":900,"Stat":"Sum"},"ReturnData":false},
 {"Id":"s","MetricStat":{"Metric":{"Namespace":"CostaLeona","MetricName":"AnswersSucceeded"},"Period":900,"Stat":"Sum"},"ReturnData":false}]
EOF
aws cloudwatch put-metric-alarm --alarm-name costaleona-answers-failed --alarm-description "More than 5% of answers failed in 15 minutes: system is up but not working" \
  --metrics file:///tmp/failrate.json --evaluation-periods 1 --threshold 5 --comparison-operator GreaterThanThreshold \
  --treat-missing-data notBreaching --alarm-actions "$TOPIC" --ok-actions "$TOPIC" --tags $TAGS
echo "alarm  costaleona-answers-failed"
# 8 Quality: scheduled smoke-test pass rate
aws cloudwatch put-metric-alarm --alarm-name costaleona-passrate-low --alarm-description "Scheduled test-question pass rate below 80%" \
  --metric-name PassRate --namespace CostaLeona --dimensions Name=TestSet,Value=smoke --statistic Minimum --period 3600 --evaluation-periods 1 --threshold 80 \
  --comparison-operator LessThanThreshold --treat-missing-data notBreaching --alarm-actions "$TOPIC" --ok-actions "$TOPIC" --tags $TAGS
echo "alarm  costaleona-passrate-low"

# Dashboard
cat > /tmp/dash.json <<EOF
{"widgets":[
 {"type":"metric","x":0,"y":0,"width":8,"height":6,"properties":{"title":"Requests answered (5 min)","region":"$R","stat":"Sum","period":300,"metrics":[["CostaLeona","AnswersSucceeded"],[".","AnswersFailed"]]}},
 {"type":"metric","x":8,"y":0,"width":8,"height":6,"properties":{"title":"Errors: failed + empty answers","region":"$R","stat":"Sum","period":300,"metrics":[["CostaLeona","AnswersFailed"],[".","EmptyAnswer"]]}},
 {"type":"metric","x":16,"y":0,"width":8,"height":6,"properties":{"title":"Response time (ms, average)","region":"$R","stat":"Average","period":300,"metrics":[["CostaLeona","ResponseTimeMs"]]}},
 {"type":"metric","x":0,"y":6,"width":8,"height":6,"properties":{"title":"EC2 CPU %","region":"$R","stat":"Average","period":300,"metrics":[["AWS/EC2","CPUUtilization","InstanceId","$IID"]]}},
 {"type":"metric","x":8,"y":6,"width":8,"height":6,"properties":{"title":"Disk used % (root)","region":"$R","stat":"Maximum","period":60,"metrics":[["CWAgent","disk_used_percent","InstanceId","$IID"]]}},
 {"type":"metric","x":16,"y":6,"width":8,"height":6,"properties":{"title":"Memory used %","region":"$R","stat":"Average","period":60,"metrics":[["CWAgent","mem_used_percent","InstanceId","$IID"]]}},
 {"type":"metric","x":0,"y":12,"width":12,"height":6,"properties":{"title":"Test-question pass rate % (scheduled)","region":"$R","stat":"Minimum","period":3600,"metrics":[["CostaLeona","PassRate","TestSet","smoke"]]}},
 {"type":"alarm","x":12,"y":12,"width":12,"height":6,"properties":{"title":"Alarm status","alarms":[
   "arn:aws:cloudwatch:$R:$(aws sts get-caller-identity --query Account --output text):alarm:costaleona-cpu-high",
   "arn:aws:cloudwatch:$R:$(aws sts get-caller-identity --query Account --output text):alarm:costaleona-disk-high",
   "arn:aws:cloudwatch:$R:$(aws sts get-caller-identity --query Account --output text):alarm:costaleona-memory-high",
   "arn:aws:cloudwatch:$R:$(aws sts get-caller-identity --query Account --output text):alarm:costaleona-answers-failed",
   "arn:aws:cloudwatch:$R:$(aws sts get-caller-identity --query Account --output text):alarm:costaleona-empty-answers",
   "arn:aws:cloudwatch:$R:$(aws sts get-caller-identity --query Account --output text):alarm:costaleona-status-check-failed"]}}]}
EOF
aws cloudwatch put-dashboard --dashboard-name CostaLeona --dashboard-body file:///tmp/dash.json >/dev/null
echo "dashboard CostaLeona created"
aws cloudwatch describe-alarms --alarm-name-prefix costaleona- --query 'MetricAlarms[].[AlarmName,StateValue]' --output table
