#!/bin/bash
# Automation 2 - scheduled test questions: asks Leona the smoke-test questions, publishes the pass rate
# to CloudWatch and emails via SNS if it drops below 80% (EventBridge -> SSM Run Command, hourly).
set -uo pipefail
LOG=/var/log/leona-automation.log
log() { echo "$(date -u +%FT%TZ) smoketest $*" | tee -a "$LOG"; }
OUT=$(docker exec costa-leona-gateway python /app/eval/run_eval.py --set smoke --publish --alert --delay 3 2>&1)
RC=$?
SUMMARY=$(echo "$OUT" | grep '^SUMMARY' | tail -1)
[ $RC -eq 0 ] && log "OK ${SUMMARY#SUMMARY }" || log "BELOW_THRESHOLD_OR_ERROR rc=$RC ${SUMMARY#SUMMARY }"
exit $RC
