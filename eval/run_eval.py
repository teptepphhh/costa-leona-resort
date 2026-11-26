"""Score the Leona gateway against labelled questions (eval/questions.csv).

A question PASSES when the answer contains every '&'-separated term, where each term may list
'|' alternatives (case-insensitive). Run inside the gateway container (or anywhere with httpx):
    python /app/eval/run_eval.py --set full            # all 30 questions
    python /app/eval/run_eval.py --set smoke --publish --alert   # scheduled smoke test
"""
import argparse
import csv
import json
import os
import re
import sys
import time
from pathlib import Path

import httpx

URL = os.getenv("GATEWAY_URL", "http://localhost:8080")
TOKEN = os.getenv("LEONA_GATEWAY_TOKEN", "")
REGION = os.getenv("AWS_REGION", "ap-southeast-1")
HERE = Path(__file__).parent


def norm(s: str) -> str:
    return re.sub(r"[\s,]+", " ", s.lower().replace(" ", " ").replace(" ", " "))


def passes(answer: str, rule: str) -> bool:
    a = norm(answer)
    return all(any(norm(alt) in a for alt in term.split("|")) for term in rule.split("&"))


def ask(q: str):
    t0 = time.perf_counter()
    r = httpx.post(f"{URL}/v1/chat/completions", headers={"Authorization": f"Bearer {TOKEN}"},
                   json={"model": "leona-1", "messages": [{"role": "user", "content": q}]}, timeout=90)
    ms = round((time.perf_counter() - t0) * 1000)
    if r.status_code != 200:
        return "", ms, r.status_code
    return r.json()["choices"][0]["message"]["content"], ms, 200


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--set", choices=["smoke", "full"], default="full")
    ap.add_argument("--publish", action="store_true", help="publish PassRate to CloudWatch")
    ap.add_argument("--alert", action="store_true", help="email via SNS if pass rate < threshold")
    ap.add_argument("--threshold", type=float, default=80.0)
    ap.add_argument("--delay", type=float, default=3.0)
    ap.add_argument("--csv", default=str(HERE / "questions.csv"))
    ap.add_argument("--out", default="")
    args = ap.parse_args()

    rows = [r for r in csv.DictReader(open(args.csv, encoding="utf-8")) if args.set == "full" or r["smoke"] == "1"]
    results, ok = [], 0
    for r in rows:
        ans, ms, status = ask(r["question"])
        p = status == 200 and passes(ans, r["must_contain"])
        ok += p
        results.append({"id": r["id"], "category": r["category"], "pass": p, "status": status, "ms": ms,
                        "question": r["question"], "answer": ans.replace("\n", " ")[:400]})
        print(f"[{'PASS' if p else 'FAIL'}] #{r['id']:>2} {r['category']:<12} {ms:>6} ms  {r['question']}", flush=True)
        time.sleep(args.delay)
    rate = round(100.0 * ok / len(rows), 1)
    summary = {"ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "set": args.set, "passed": ok,
               "total": len(rows), "pass_rate": rate}
    print("SUMMARY", json.dumps(summary))
    if args.out:
        Path(args.out).write_text(json.dumps({"summary": summary, "results": results}, indent=2, ensure_ascii=False), encoding="utf-8")
    if args.publish or args.alert:
        import boto3
        if args.publish:
            boto3.client("cloudwatch", region_name=REGION).put_metric_data(
                Namespace="CostaLeona", MetricData=[{"MetricName": "PassRate", "Value": rate, "Unit": "Percent",
                                                      "Dimensions": [{"Name": "TestSet", "Value": args.set}]}])
        if args.alert and rate < args.threshold:
            topic = boto3.client("ssm", region_name=REGION).get_parameter(Name="/costaleona/alert_topic")["Parameter"]["Value"]
            fails = "\n".join(f"- #{x['id']} {x['question']}" for x in results if not x["pass"])
            boto3.client("sns", region_name=REGION).publish(
                TopicArn=topic, Subject="Costa Leona: test-question pass rate below threshold",
                Message=f"Pass rate {rate}% ({ok}/{len(rows)}) is below {args.threshold}%.\nFailed:\n{fails}")
    sys.exit(0 if rate >= args.threshold else 1)


if __name__ == "__main__":
    main()
