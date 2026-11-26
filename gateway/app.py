"""Leona gateway - Costa Leona Resort front-desk assistant.

An OpenAI-compatible shim that sits between LibreChat and the Gemini API.
It (1) loads the resort knowledge base from S3 (or a local folder),
(2) reads the model key from SSM Parameter Store (or an env var locally),
(3) writes one JSON log line per request, and
(4) publishes CloudWatch custom metrics (AnswersSucceeded/AnswersFailed/EmptyAnswer).
No secret is stored in this file or in the repository.
"""
import asyncio
import hashlib
import json
import logging
import os
import threading
import time
import uuid
from pathlib import Path

import httpx
from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.responses import JSONResponse, StreamingResponse

APP_VERSION = os.getenv("APP_VERSION", "1.0.0")
MODEL = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite")
FALLBACK_MODEL = os.getenv("GEMINI_FALLBACK_MODEL", "")
REGION = os.getenv("AWS_REGION", "ap-southeast-1")
KNOWLEDGE_BUCKET = os.getenv("KNOWLEDGE_BUCKET", "")
KNOWLEDGE_PREFIX = os.getenv("KNOWLEDGE_PREFIX", "knowledge/")
KNOWLEDGE_DIR = Path(os.getenv("KNOWLEDGE_DIR", "/app/knowledge"))
KEY_SSM_PARAM = os.getenv("GEMINI_KEY_SSM_PARAM", "")        # e.g. /costaleona/gemini_api_key
TOKEN_SSM_PARAM = os.getenv("GATEWAY_TOKEN_SSM_PARAM", "")   # e.g. /costaleona/gateway_token
CW_METRICS = os.getenv("CW_METRICS", "0") == "1"
REQUEST_LOG = os.getenv("REQUEST_LOG", "/var/log/leona/requests.log")

SYSTEM_PROMPT = """You are Leona, the virtual front-desk assistant of Costa Leona Resort, a fictional beach resort.
Answer guests' questions ONLY from the RESORT KNOWLEDGE below. Be warm, brief and practical.
Rules:
- If the answer is not in the knowledge, say you do not have that information and give the front desk contact. Never guess prices, times or policies.
- You are informational only. You cannot confirm, change or cancel bookings, take payments, or decide anything about a person.
- Never ask for, and tell guests not to share, ID numbers, card numbers, passwords or health details.
- Do not give medical, legal or safety-critical advice; for emergencies point to the emergency contacts in the knowledge.
- Reply in the language the guest uses (English or Filipino).
"""

os.makedirs(os.path.dirname(REQUEST_LOG), exist_ok=True)
req_logger = logging.getLogger("leona.requests")
req_logger.setLevel(logging.INFO)
if not req_logger.handlers:
    # NOTE: plain FileHandler on purpose (no rotation) - the incident/runbook documents the later fix.
    req_logger.addHandler(logging.FileHandler(REQUEST_LOG))
    req_logger.addHandler(logging.StreamHandler())
app = FastAPI(title="Leona gateway")

_cache = {"key": None, "token": None, "kb": None, "kb_at": 0.0, "kb_hash": "none"}
_lock = threading.Lock()


def _ssm_get(name: str) -> str:
    import boto3
    return boto3.client("ssm", region_name=REGION).get_parameter(Name=name, WithDecryption=True)["Parameter"]["Value"]


def gemini_key() -> str:
    if _cache["key"] is None:
        _cache["key"] = _ssm_get(KEY_SSM_PARAM) if KEY_SSM_PARAM else os.environ["GEMINI_API_KEY"]
    return _cache["key"]


def gateway_token() -> str:
    if _cache["token"] is None:
        _cache["token"] = _ssm_get(TOKEN_SSM_PARAM) if TOKEN_SSM_PARAM else os.getenv("LEONA_GATEWAY_TOKEN", "")
    return _cache["token"]


def load_knowledge() -> str:
    with _lock:
        if _cache["kb"] is not None and time.time() - _cache["kb_at"] < 300:
            return _cache["kb"]
        docs = []
        if KNOWLEDGE_BUCKET:
            import boto3
            s3 = boto3.client("s3", region_name=REGION)
            for page in s3.get_paginator("list_objects_v2").paginate(Bucket=KNOWLEDGE_BUCKET, Prefix=KNOWLEDGE_PREFIX):
                for obj in page.get("Contents", []):
                    if obj["Key"].endswith(".md"):
                        body = s3.get_object(Bucket=KNOWLEDGE_BUCKET, Key=obj["Key"])["Body"].read().decode("utf-8")
                        docs.append((obj["Key"], body))
        elif KNOWLEDGE_DIR.exists():
            for p in sorted(KNOWLEDGE_DIR.glob("*.md")):
                docs.append((p.name, p.read_text(encoding="utf-8")))
        text = "\n\n".join(f"### {name}\n{body}" for name, body in sorted(docs))
        _cache.update(kb=text, kb_at=time.time(), kb_hash=hashlib.sha256(text.encode()).hexdigest()[:8])
        return text


def put_metrics(success: bool, empty: bool, ms: float):
    if not CW_METRICS:
        return

    def _send():
        try:
            import boto3
            data = [
                {"MetricName": "AnswersSucceeded", "Value": 1 if success else 0, "Unit": "Count"},
                {"MetricName": "AnswersFailed", "Value": 0 if success else 1, "Unit": "Count"},
                {"MetricName": "EmptyAnswer", "Value": 1 if empty else 0, "Unit": "Count"},
                {"MetricName": "ResponseTimeMs", "Value": ms, "Unit": "Milliseconds"},
            ]
            boto3.client("cloudwatch", region_name=REGION).put_metric_data(Namespace="CostaLeona", MetricData=data)
        except Exception:
            pass

    threading.Thread(target=_send, daemon=True).start()


def to_gemini(messages):
    contents = []
    for m in messages:
        role = m.get("role")
        if role == "system":
            continue
        content = m.get("content")
        if isinstance(content, list):
            content = " ".join(p.get("text", "") for p in content if isinstance(p, dict))
        contents.append({"role": "model" if role == "assistant" else "user", "parts": [{"text": content or ""}]})
    return contents


async def ask_gemini(messages):
    system = SYSTEM_PROMPT + "\nRESORT KNOWLEDGE:\n" + load_knowledge()
    body = {"systemInstruction": {"parts": [{"text": system}]}, "contents": to_gemini(messages),
            "generationConfig": {"temperature": 0.2, "maxOutputTokens": 600}}
    models = [MODEL] + ([FALLBACK_MODEL] if FALLBACK_MODEL else [])
    last_err, status = "unknown", 502
    async with httpx.AsyncClient(timeout=40) as client:
        for model in models:
            for attempt in range(3):
                r = await client.post(
                    f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
                    headers={"x-goog-api-key": gemini_key()}, json=body)
                status = r.status_code
                if r.status_code == 200:
                    parts = (r.json().get("candidates") or [{}])[0].get("content", {}).get("parts", [])
                    return "".join(p.get("text", "") for p in parts).strip(), model, 200, ""
                last_err = r.text[:200].replace("\n", " ")
                if r.status_code not in (429, 500, 503):
                    break
                await asyncio.sleep(1.5 * (attempt + 1))
    return "", MODEL, status, last_err


@app.get("/health")
def health():
    return {"status": "ok", "version": APP_VERSION, "knowledge": _cache["kb_hash"]}


@app.get("/v1/models")
def models():
    return {"object": "list", "data": [{"id": "leona-1", "object": "model", "owned_by": "costa-leona"}]}


@app.post("/v1/chat/completions")
async def chat(request: Request, authorization: str = Header(default="")):
    tok = gateway_token()
    if tok and authorization != f"Bearer {tok}":
        raise HTTPException(status_code=401, detail="unauthorized")
    payload = await request.json()
    messages = payload.get("messages", [])
    question = next((m.get("content") for m in reversed(messages) if m.get("role") == "user"), "")
    if isinstance(question, list):
        question = " ".join(p.get("text", "") for p in question if isinstance(p, dict))
    rid = uuid.uuid4().hex[:12]
    t0 = time.perf_counter()
    answer, model_used, status, err = await ask_gemini(messages)
    ms = round((time.perf_counter() - t0) * 1000)
    success, empty = status == 200 and bool(answer), status == 200 and not answer
    req_logger.info(json.dumps({
        "ts": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "request_id": rid, "question": (question or "")[:300],
        "duration_ms": ms, "success": success, "empty": empty, "status": status, "model": model_used,
        "version": f"{APP_VERSION}+kb.{_cache['kb_hash']}", "error": err}, ensure_ascii=False))
    put_metrics(success, empty, ms)
    if not success:
        return JSONResponse(status_code=429 if status == 429 else 502,
                            content={"error": {"message": f"Model provider error (status {status}). Please try again.",
                                               "type": "upstream_error"}})
    created = int(time.time())
    if payload.get("stream"):
        def sse():
            for i in range(0, len(answer), 40):
                chunk = {"id": rid, "object": "chat.completion.chunk", "created": created, "model": "leona-1",
                         "choices": [{"index": 0, "delta": {"content": answer[i:i + 40]}, "finish_reason": None}]}
                yield f"data: {json.dumps(chunk, ensure_ascii=False)}\n\n"
            end = {"id": rid, "object": "chat.completion.chunk", "created": created, "model": "leona-1",
                   "choices": [{"index": 0, "delta": {}, "finish_reason": "stop"}]}
            yield f"data: {json.dumps(end)}\n\ndata: [DONE]\n\n"

        return StreamingResponse(sse(), media_type="text/event-stream")
    return {"id": rid, "object": "chat.completion", "created": created, "model": "leona-1",
            "choices": [{"index": 0, "message": {"role": "assistant", "content": answer}, "finish_reason": "stop"}],
            "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}}
