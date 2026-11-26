#!/bin/bash
# WS-F step 1 - CAUSE THE FAULT (safe, own account, Appendix E "Disk full").
# Simulates months of request-log growth: appends synthetic log lines to the same unrotated file the gateway
# writes (/opt/leona/logs/gateway/requests.log) until only ~400 MB of the root disk is left.
set -uo pipefail
LOGF=/opt/leona/logs/gateway/requests.log
echo "FAULT_START $(date -u +%FT%TZ)" | tee -a /var/log/leona-automation.log
df -h / | tail -1
LINE='{"ts":"2026-11-26T00:00:00+0000","request_id":"synthetic0001","question":"synthetic load line to simulate long-term log growth ................................................................","duration_ms":4200,"success":true,"empty":false,"status":200,"model":"gemini-3.5-flash-lite","version":"1.0.0","error":""}'
while [ "$(df --output=avail -m / | tail -1 | tr -d ' ')" -gt 400 ]; do
  yes "$LINE" | head -c 500000000 >> "$LOGF"
done
echo "FAULT_DISK_FULL $(date -u +%FT%TZ)" | tee -a /var/log/leona-automation.log
df -h / | tail -1
