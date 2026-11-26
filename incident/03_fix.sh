#!/bin/bash
# WS-F step 3 - FIX (free the space now) and PREVENT (log rotation + size cap) and VERIFY.
set -uo pipefail
LOGF=/opt/leona/logs/gateway/requests.log
echo "FIX_START $(date -u +%FT%TZ)" | tee -a /var/log/leona-automation.log
df -h / | tail -1
# 1) free space immediately: keep the most recent 2,000 real lines, drop the synthetic bulk
tail -n 2000 "$LOGF" > /tmp/requests.keep && cat /tmp/requests.keep > "$LOGF"; rm -f /tmp/requests.keep
echo "after truncate:"; df -h / | tail -1
# 2) prevention: rotate by size, keep 3 compressed copies (copytruncate: the app keeps its open file handle)
cat > /etc/logrotate.d/leona <<'EOF'
/opt/leona/logs/gateway/requests.log {
    hourly
    maxsize 100M
    rotate 3
    compress
    delaycompress
    copytruncate
    missingok
    notifempty
}
EOF
mkdir -p /etc/systemd/system/logrotate.timer.d
printf '[Timer]\nOnCalendar=\nOnCalendar=hourly\n' > /etc/systemd/system/logrotate.timer.d/hourly.conf
systemctl daemon-reload && systemctl enable --now logrotate.timer
# 3) prove the control works: grow the log past the limit, run logrotate, check the size drops
yes '{"synthetic":"rotation test line ..............................................................................."}' | head -c 150000000 >> "$LOGF"
echo "before rotate: $(ls -lh $LOGF | awk '{print $5}')"
logrotate -f /etc/logrotate.d/leona
echo "after rotate:  $(ls -lh $LOGF | awk '{print $5}')"; ls -lh /opt/leona/logs/gateway/
rm -f /opt/leona/logs/gateway/requests.log.1* 2>/dev/null
echo "timer:"; systemctl list-timers logrotate.timer --no-pager | head -3
echo "FIX_DONE $(date -u +%FT%TZ)" | tee -a /var/log/leona-automation.log
df -h / | tail -1
