#!/bin/bash
# Restore test (database): take a fresh backup, restore the newest S3 backup into a brand-new empty MongoDB
# container and prove the data came back. Run on the instance (SSM) - prints timings for RTO.
set -uo pipefail
export AWS_DEFAULT_REGION=ap-southeast-1
LOG=/var/log/leona-automation.log
say() { echo "[$(date -u +%FT%TZ)] $*" | tee -a "$LOG"; }
BUCKET=$(aws ssm get-parameter --name /costaleona/bucket --query Parameter.Value --output text)
counts() { docker exec "$1" mongosh --quiet --eval "const d=db.getSiblingDB('CostaLeona'); print(['users','conversations','messages'].map(c=>c+'='+d.getCollection(c).countDocuments()).join(' '))"; }
T0=$(date +%s)

say "STEP 1 take a fresh backup so live and backup can be compared exactly"
bash /opt/leona/automation/backup.sh
KEY=$(aws s3 ls "s3://$BUCKET/backups/mongo/" | sort | tail -1 | awk '{print $4}')
say "newest backup object: $KEY"
LIVE=$(counts costa-leona-db); say "LIVE database counts:     $LIVE"

say "STEP 2 start a brand-new empty MongoDB container (no volume, no network)"
docker rm -f mongo-restore-test >/dev/null 2>&1
docker run -d --name mongo-restore-test --network none docker.io/library/mongo:8.0.20 mongod --noauth >/dev/null
for i in $(seq 1 30); do docker exec mongo-restore-test mongosh --quiet --eval 'db.runCommand({ping:1}).ok' 2>/dev/null | grep -q 1 && break; sleep 2; done
say "empty container counts: $(counts mongo-restore-test)"

say "STEP 3 restore from s3://$BUCKET/backups/mongo/$KEY"
T1=$(date +%s)
aws s3 cp "s3://$BUCKET/backups/mongo/$KEY" - --only-show-errors | docker exec -i mongo-restore-test mongorestore --archive --gzip 2>&1 | tail -3
T2=$(date +%s)
RESTORED=$(counts mongo-restore-test); say "RESTORED database counts: $RESTORED"

say "STEP 4 check the guest-desk account exists in the restored data"
docker exec mongo-restore-test mongosh --quiet --eval "printjson(db.getSiblingDB('CostaLeona').users.find({email:'admin@costaleona.example'},{_id:0,email:1,name:1,role:1}).toArray())"

if [ "$LIVE" = "$RESTORED" ]; then say "RESULT PASS - live and restored counts are identical"; RC=0; else say "RESULT FAIL - counts differ"; RC=1; fi
say "TIMING restore step $((T2-T1)) s; whole procedure $(( $(date +%s)-T0 )) s (RTO evidence)"
docker rm -f mongo-restore-test >/dev/null 2>&1 && say "cleanup: test container removed"
exit $RC
