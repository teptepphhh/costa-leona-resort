#!/bin/bash
# WS-D control: check that nothing personal is being logged or sent on. Scans every question recorded in the
# request log (and rotated copies) for e-mail addresses, phone numbers, and long digit strings (card/ID numbers).
# The resort's own fictional contact details are allowed because they are in the answers, not the questions.
LOG=/opt/leona/logs/gateway
docker exec costa-leona-gateway python - <<'PY'
import glob, json, re
pats = {"email": r"[\w.+-]+@[\w-]+\.[\w.]+", "phone": r"(\+?63|0)9\d{9}|\+\d[\d\s-]{9,}", "long_digits": r"\b\d{9,19}\b"}
total = hits = 0
for f in glob.glob("/var/log/leona/requests.log*"):
    if f.endswith(".gz"):
        continue
    for line in open(f, errors="ignore"):
        try:
            q = json.loads(line).get("question", "")
        except Exception:
            continue
        if q.startswith("synthetic"):
            continue
        total += 1
        for name, p in pats.items():
            if re.search(p, q):
                hits += 1
                print("POSSIBLE PERSONAL DATA (", name, "):", q[:80])
print(f"PII CHECK: scanned {total} logged questions, {hits} possible personal-data hits")
PY
