"""The same Quillnote help assistant as an HTTP endpoint, so scripts/acceptance.py can test the live app.

Run locally:  uvicorn app.api:app --port 8000      (from the kit folder)
Endpoints:
  GET  /        a small page with a question box (the live app people can try)
  POST /ask     JSON {"question": "..."} -> {"text", "cited", "fallback", "model"}
  GET  /health  {"ok": true}
It calls the same answer() as app/app.py, with the same prompt file, search and fallbacks.
Spend guard: each client gets MAX_CALLS_PER_CLIENT model calls per day, and the whole app gets MAX_CALLS_PER_DAY.
"""
import datetime as dt
import os
import sys
import threading
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from fastapi import FastAPI, Request  # noqa: E402
from fastapi.responses import HTMLResponse, JSONResponse  # noqa: E402
from pydantic import BaseModel  # noqa: E402

from app import app as core  # noqa: E402

# Config you can change, or set as environment variables on your host.
MAX_CALLS_PER_CLIENT = int(os.environ.get("MAX_CALLS_PER_CLIENT", "30"))  # per client per UTC day
MAX_CALLS_PER_DAY = int(os.environ.get("MAX_CALLS_PER_DAY", "300"))  # for the whole app per UTC day
MAX_QUESTION_CHARS = 1000

app = FastAPI(title="Quillnote help assistant")
_lock = threading.Lock()
_counts = {"day": None, "total": 0, "clients": {}}


class Ask(BaseModel):
    question: str


def client_id(request):
    # Hosts like Render and Hugging Face put the real client address in X-Forwarded-For.
    forwarded = request.headers.get("x-forwarded-for", "")
    return forwarded.split(",")[0].strip() or (request.client.host if request.client else "unknown")


def spend_guard_allows(client):
    """Count one call for this client. False when the client or the app is over today's limit."""
    today = dt.datetime.now(dt.timezone.utc).date().isoformat()
    with _lock:
        if _counts["day"] != today:
            _counts.update(day=today, total=0, clients={})
        used = _counts["clients"].get(client, 0)
        if used >= MAX_CALLS_PER_CLIENT or _counts["total"] >= MAX_CALLS_PER_DAY:
            return False
        _counts["clients"][client] = used + 1
        _counts["total"] += 1
        return True


@app.get("/health")
def health():
    return {"ok": True, "prompt": core.PROMPT_FILE.name}


@app.post("/ask")
def ask(body: Ask, request: Request):
    question = body.question.strip()[:MAX_QUESTION_CHARS]
    if not question:
        return JSONResponse({"text": "Ask a question first.", "cited": [], "fallback": "empty", "model": None}, 400)
    if not spend_guard_allows(client_id(request)):
        reply = {"text": "Spend guard: today's call limit is used up. Try again tomorrow.", "cited": [],
                 "fallback": "spend_guard", "model": None}
        return JSONResponse(reply, 429)
    r = core.answer(question)
    return {"text": r["text"], "cited": r["cited"], "fallback": r["fallback"],
            "model": r["call"]["model"] if r["call"] else None}


PAGE = """<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Quillnote help assistant</title>
<style>body{font-family:system-ui,sans-serif;max-width:640px;margin:2rem auto;padding:0 1rem;line-height:1.5}
input{width:100%;padding:.5rem;font-size:1rem}button{margin-top:.5rem;padding:.5rem 1rem;font-size:1rem}
#out{white-space:pre-wrap;margin-top:1rem}small{color:#555}</style></head><body>
<h1>Quillnote help assistant</h1><p><small>Answers come only from the Quillnote help pages. Demo app with synthetic data.</small></p>
<form id="f"><input id="q" placeholder="Your question" autocomplete="off"><button>Ask</button></form>
<div id="out"></div><p><small id="meta"></small></p>
<script>
document.getElementById("f").onsubmit = async (e) => {
  e.preventDefault();
  const out = document.getElementById("out"), meta = document.getElementById("meta");
  out.textContent = "Thinking..."; meta.textContent = "";
  const r = await fetch("ask", {method: "POST", headers: {"Content-Type": "application/json"},
    body: JSON.stringify({question: document.getElementById("q").value})});
  const d = await r.json();
  out.textContent = d.text;
  meta.textContent = d.fallback ? "Fallback used: " + d.fallback : "Pages cited: " + (d.cited.join(", ") || "none");
};
</script></body></html>"""


@app.get("/", response_class=HTMLResponse)
def home():
    return PAGE
