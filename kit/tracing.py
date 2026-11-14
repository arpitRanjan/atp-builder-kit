"""Spans for the kit app: one JSON line per timed step of a request, written to traces/spans.jsonl.

Span names: request (the whole request), retrieval, model_call, tool_call.
Each line has trace_id, span_id, parent_id, name, start, latency_ms, input_tokens, output_tokens,
cached_tokens, cost_usd, model, ttft_ms, status and attrs. A child span is written before its parent,
because it finishes first.

notebooks/10_tracing.ipynb uses this file. `make traces` runs:
    python -m kit.tracing --requests 20 --out traces/spans.jsonl
"""
import argparse
import csv
import json
import re
import sys
import time
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from kit.llm import call_llm  # noqa: E402
from kit.prices import cost  # noqa: E402

SPAN_NAMES = ("request", "retrieval", "model_call", "tool_call")
FIELDS = ["trace_id", "span_id", "parent_id", "name", "start", "latency_ms", "input_tokens", "output_tokens",
          "cached_tokens", "cost_usd", "model", "ttft_ms", "status", "attrs"]

# 20 requests: 17 questions with the page that answers them, and 3 that ask the app to draft an issue.
DEFAULT_REQUESTS = [
    {"question": "How do I create a new note and rename it later?", "expect": "qn-01"},
    {"question": "How do I export one of my notes as a PDF file?", "expect": "qn-02"},
    {"question": "Is there a way to save a note as PDF for printing?", "expect": "qn-02"},
    {"question": "How do tags work, and can I organize notes into folders too?", "expect": "qn-03"},
    {"question": "How can I search for a note by keyword?", "expect": "qn-04"},
    {"question": "Why aren't my latest notes showing up on my other device, and how do I fix sync?", "expect": "qn-05"},
    {"question": "How do I switch the app to dark mode?", "expect": "qn-06"},
    {"question": "Can I change the theme colors in the app?", "expect": "qn-06"},
    {"question": "I deleted a note by accident. Can I get it back?", "expect": "qn-07"},
    {"question": "Will the app still work if I have no internet connection?", "expect": "qn-08"},
    {"question": "Where can I see the different plans and subscription prices?", "expect": "qn-09"},
    {"question": "How do I share a notebook with my team members?", "expect": "qn-10"},
    {"question": "Can I invite coworkers to a shared notebook and control what they can access?", "expect": "qn-10"},
    {"question": "What roles are available for team members, and what can each role do?", "expect": "qn-11"},
    {"question": "How do shared templates work for a team workspace?", "expect": "qn-12"},
    {"question": "Can our team create templates that everyone in the workspace can use?", "expect": "qn-12"},
    {"question": "How can I organize notes with tags and then find them quickly with search?", "expect": "qn-03"},
    {"question": 'PDF export cuts off wide tables. Draft an issue titled "PDF export cuts off tables".', "issue": True},
    {"question": 'Sync fails on Android. Draft an issue titled "Android sync fails".', "issue": True},
    {"question": 'Dark mode resets after a restart. Draft an issue titled "Dark mode resets".', "issue": True},
]


class Tracer:
    """Writes one JSON line per span to `path` (appends, so several runs can share a file)."""

    def __init__(self, path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.written = []  # the spans this tracer wrote, kept in memory too

    def new_trace(self):
        return uuid.uuid4().hex[:12]

    @contextmanager
    def span(self, name, trace_id, parent_id=None, **attrs):
        rec = {"trace_id": trace_id, "span_id": uuid.uuid4().hex[:8], "parent_id": parent_id, "name": name,
               "start": datetime.now(timezone.utc).isoformat(timespec="milliseconds"), "latency_ms": None,
               "input_tokens": 0, "output_tokens": 0, "cached_tokens": 0, "cost_usd": 0.0, "model": None,
               "ttft_ms": None, "status": "ok", "attrs": dict(attrs)}
        start = time.perf_counter()
        try:
            yield rec
        except Exception as e:
            rec["status"] = f"error: {type(e).__name__}: {e}"[:200]
            raise
        finally:
            if rec["latency_ms"] is None:  # a span can set its own latency (the model call does)
                rec["latency_ms"] = round((time.perf_counter() - start) * 1000, 1)
            with open(self.path, "a") as f:
                f.write(json.dumps(rec) + "\n")
            self.written.append(rec)


def draft_issue(outbox, title, body):
    # Writes ONLY to a local file. Nothing is sent anywhere.
    with open(outbox, "a") as f:
        f.write(json.dumps({"title": title, "body": body}) + "\n")
    return {"saved": True}


def traced_answer(question, tracer, folder=None, model=None, provider=None, stream=True):
    """The app's answer function (app/app.py) with a span around each step. Returns text, cited, trace_id."""
    from app.app import SYSTEM, TOP_K, build_prompt
    from mcp_server.server import search

    trace_id = tracer.new_trace()
    with tracer.span("request", trace_id, question=question[:200]) as req:
        wall_start = time.perf_counter()
        with tracer.span("retrieval", trace_id, req["span_id"], top_k=TOP_K) as ret:
            hits = search(question, TOP_K, folder)
            ret["attrs"]["hits"] = [h["id"] for h in hits]
        text, cited, simulated_ms = "No help page matches that question.", [], 0.0
        if hits:
            with tracer.span("model_call", trace_id, req["span_id"]) as m:
                call_start = time.perf_counter()
                call = call_llm(build_prompt(question, hits), system=SYSTEM, max_output_tokens=400,
                                model=model, provider=provider, stream=stream)
                wall_ms = (time.perf_counter() - call_start) * 1000
                cached = call["cached_tokens"] or 0
                m.update(model=call["model"], input_tokens=call["input_tokens"], output_tokens=call["output_tokens"],
                         cached_tokens=cached, latency_ms=round(call["latency_s"] * 1000, 1),
                         ttft_ms=round(call["ttft_s"] * 1000, 1),
                         cost_usd=cost(call["input_tokens"], call["output_tokens"], call["model"], cached))
                m["attrs"].update(provider=call["provider"], ttft_kind=call["ttft_kind"],
                                  stop_reason=str(call["stop_reason"]),
                                  cached_reported=call["cached_tokens"] is not None)
                # The mock reports a made up latency without waiting; add the difference to the request.
                simulated_ms = max(0.0, m["latency_ms"] - wall_ms)
            text = call["text"]
            found = set(re.findall(r"qn-\d+", text))
            cited = [h["id"] for h in hits if h["id"] in found] or [h["id"] for h in hits]
        issue = re.search(r'[Dd]raft an issue titled "(.+?)"', question)
        if issue:
            with tracer.span("tool_call", trace_id, req["span_id"], tool="draft_issue") as t:
                body = f"From the help assistant. Related pages: {', '.join(cited) or 'none'}."
                t["attrs"]["result"] = draft_issue(tracer.path.parent / "outbox.jsonl", issue.group(1), body)
        children = [s for s in tracer.written if s["trace_id"] == trace_id]
        for key in ("input_tokens", "output_tokens", "cached_tokens", "cost_usd"):
            req[key] = sum(c[key] for c in children)
        model_span = next((c for c in children if c["name"] == "model_call"), None)
        retrieval_ms = next(c["latency_ms"] for c in children if c["name"] == "retrieval")
        req["latency_ms"] = round((time.perf_counter() - wall_start) * 1000 + simulated_ms, 1)
        if model_span:
            req["model"] = model_span["model"]
            req["ttft_ms"] = round(retrieval_ms + model_span["ttft_ms"], 1)  # from request start to first token
            req["attrs"]["ttft_kind"] = model_span["attrs"]["ttft_kind"]
        req["attrs"]["cited"] = cited
    return {"trace_id": trace_id, "text": text, "cited": cited}


def load_spans(path):
    path = Path(path)
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def percentile(values, p):
    """The p-th percentile (0 to 100) with linear interpolation, like numpy's default."""
    vals = sorted(v for v in values if v is not None)
    if not vals:
        return None
    pos = (len(vals) - 1) * p / 100
    low = int(pos)
    high = min(low + 1, len(vals) - 1)
    return vals[low] + (vals[high] - vals[low]) * (pos - low)


def passed(request, result, spans):
    """Success check for one request: it cited the expected page, or its draft_issue tool call worked."""
    if request.get("issue"):
        return any(s["trace_id"] == result["trace_id"] and s["name"] == "tool_call" and s["status"] == "ok"
                   for s in spans)
    return request["expect"] in result["cited"]


def summarize(spans, successes=None):
    """Latency percentiles, time to first token, cost per request and per successful task."""
    reqs = [s for s in spans if s["name"] == "request"]
    total = sum(s["cost_usd"] for s in reqs)
    n_ok = sum(1 for s in reqs if successes is None or successes.get(s["trace_id"]))
    spend = {}
    for s in spans:
        if s["name"] != "request":
            spend[s["name"]] = spend.get(s["name"], 0.0) + s["cost_usd"]
    lat = [s["latency_ms"] for s in reqs]
    ttft = [s["ttft_ms"] for s in reqs]
    return {"requests": len(reqs), "successes": n_ok,
            "p50_latency_ms": percentile(lat, 50), "p95_latency_ms": percentile(lat, 95),
            "p50_ttft_ms": percentile(ttft, 50), "p95_ttft_ms": percentile(ttft, 95),
            "ttft_kind": sorted({s["attrs"].get("ttft_kind") for s in reqs if s["attrs"].get("ttft_kind")}),
            "cost_total_usd": total, "cost_per_request_usd": total / len(reqs) if reqs else None,
            "cost_per_successful_task_usd": total / n_ok if n_ok else None, "spend_by_span_usd": spend}


def export_csv(spans, path):
    """Flat CSV of the spans (attrs as JSON text), for a spreadsheet or a BI tool."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        for s in spans:
            w.writerow({**s, "attrs": json.dumps(s["attrs"])})
    return path


def run(n, out, stream=True):
    """Send n requests (the 20 defaults, repeated if n is bigger) and write their spans to a fresh file."""
    out = Path(out)
    out.unlink(missing_ok=True)
    (out.parent / "outbox.jsonl").unlink(missing_ok=True)
    tracer = Tracer(out)
    results = []
    for i in range(n):
        req = DEFAULT_REQUESTS[i % len(DEFAULT_REQUESTS)]
        results.append((req, traced_answer(req["question"], tracer, stream=stream)))
    spans = load_spans(out)
    successes = {r["trace_id"]: passed(req, r, spans) for req, r in results}
    return spans, summarize(spans, successes)


def main(argv=None):
    parser = argparse.ArgumentParser(description="Send traced requests through the app and export the spans.")
    parser.add_argument("--requests", type=int, default=20)
    parser.add_argument("--out", default=str(ROOT / "traces" / "spans.jsonl"))
    args = parser.parse_args(argv)
    spans, summary = run(args.requests, args.out)
    csv_path = export_csv(spans, Path(args.out).with_suffix(".csv"))
    print(f"Wrote {len(spans)} spans to {args.out} and {csv_path}")
    for key, value in summary.items():
        print(f"  {key}: {round(value, 6) if isinstance(value, float) else value}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
