#!/bin/bash
# WS-F step 2 - INVESTIGATE (read-only commands used to find the root cause).
echo "### df -h /";                        df -h /
echo "### biggest directories under /opt/leona and /var/lib/docker"; du -xsh /opt/leona/logs/* /var/lib/docker/volumes/* /var/lib/docker/containers 2>/dev/null | sort -h | tail -6
echo "### biggest files in the log directory"; ls -lhS /opt/leona/logs/gateway | head -5
echo "### last line of the huge file";     tail -c 300 /opt/leona/logs/gateway/requests.log
echo "### is any rotation configured?";    ls /etc/logrotate.d/ ; grep -rl leona /etc/logrotate.d/ 2>/dev/null || echo "NO logrotate config mentions the Leona request log"
echo "### code path that writes it";       grep -n "FileHandler" /opt/leona/gateway/app.py
echo "### can the app still answer?"
docker exec costa-leona-gateway python - <<'PY'
import os, httpx
r = httpx.post("http://localhost:8080/v1/chat/completions", headers={"Authorization": "Bearer " + os.environ["LEONA_GATEWAY_TOKEN"]},
               json={"model": "leona-1", "messages": [{"role": "user", "content": "What time is check-in?"}]}, timeout=60)
print(r.status_code, r.text[:200])
PY
echo "### mongo able to write?"; docker exec costa-leona-db mongosh --quiet --eval "try{db.getSiblingDB('probe').t.insertOne({x:1});print('write ok')}catch(e){print('WRITE FAILED: '+e.message)}"
docker exec costa-leona-db mongosh --quiet --eval "db.getSiblingDB('probe').dropDatabase()" >/dev/null 2>&1
