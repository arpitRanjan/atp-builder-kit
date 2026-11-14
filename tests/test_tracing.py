# kit/tracing.py: spans, percentiles, the summary and the CLI behind `make traces`.
import json

from conftest import ROOT

from kit import tracing
from kit.llm import call_llm
from kit.prices import cost

FIXTURES = ROOT / "tests" / "fixtures" / "corpus"


def test_span_writes_one_line_with_latency(tmp_path):
    tracer = tracing.Tracer(tmp_path / "spans.jsonl")
    with tracer.span("retrieval", "t1", "p1", top_k=3) as s:
        s["attrs"]["hits"] = ["qn-01"]
    rec = json.loads((tmp_path / "spans.jsonl").read_text())
    assert set(tracing.FIELDS) == set(rec)
    assert rec["name"] == "retrieval" and rec["parent_id"] == "p1" and rec["latency_ms"] >= 0
    assert rec["attrs"] == {"top_k": 3, "hits": ["qn-01"]}


def test_failed_span_is_still_written(tmp_path):
    tracer = tracing.Tracer(tmp_path / "spans.jsonl")
    try:
        with tracer.span("tool_call", "t1"):
            raise TimeoutError("slow")
    except TimeoutError:
        pass
    assert tracing.load_spans(tmp_path / "spans.jsonl")[0]["status"].startswith("error: TimeoutError")


def test_traced_answer_spans(tmp_path):
    tracer = tracing.Tracer(tmp_path / "spans.jsonl")
    out = tracing.traced_answer('PDF cut off. Draft an issue titled "PDF bug".', tracer, folder=FIXTURES)
    spans = tracing.load_spans(tmp_path / "spans.jsonl")
    assert [s["name"] for s in spans] == ["retrieval", "model_call", "tool_call", "request"]
    req, model = spans[-1], spans[1]
    assert {s["trace_id"] for s in spans} == {out["trace_id"]}
    assert all(s["parent_id"] == req["span_id"] for s in spans[:-1])
    assert req["cost_usd"] == model["cost_usd"] > 0 and req["input_tokens"] == model["input_tokens"]
    assert req["ttft_ms"] <= req["latency_ms"] and model["ttft_ms"] < model["latency_ms"]
    assert (tmp_path / "outbox.jsonl").exists()


def test_percentile_matches_numpy_default():
    assert tracing.percentile([1, 2, 3, 4], 50) == 2.5
    assert tracing.percentile([10, 20, 30, 40, 50], 95) == 48.0
    assert tracing.percentile([], 50) is None


def test_summary_cost_per_successful_task():
    spans = [{"name": "request", "trace_id": t, "latency_ms": ms, "ttft_ms": ms / 2, "cost_usd": 0.01, "attrs": {}}
             for t, ms in [("a", 100), ("b", 200), ("c", 300), ("d", 400)]]
    spans.append({"name": "model_call", "trace_id": "a", "cost_usd": 0.01, "attrs": {}})
    s = tracing.summarize(spans, {"a": True, "b": True, "c": False, "d": False})
    assert s["cost_per_request_usd"] == 0.01 and abs(s["cost_per_successful_task_usd"] - 0.02) < 1e-12
    assert s["p50_latency_ms"] == 250 and s["spend_by_span_usd"] == {"model_call": 0.01}


def test_cli_writes_spans_and_csv(tmp_path, capsys):
    out = tmp_path / "traces" / "spans.jsonl"
    assert tracing.main(["--requests", "20", "--out", str(out)]) == 0
    spans = tracing.load_spans(out)
    assert sum(s["name"] == "request" for s in spans) == 20
    assert {s["name"] for s in spans} == set(tracing.SPAN_NAMES)
    assert out.with_suffix(".csv").read_text().splitlines()[0].startswith("trace_id,span_id")
    assert "cost_per_successful_task_usd" in capsys.readouterr().out


def test_mock_reports_cached_tokens_and_cached_cost():
    prefix = "stable instructions and pages. " * 200  # about 1500 tokens
    first = call_llm("question one", system=prefix)
    again = call_llm("question two", system=prefix)
    changed = call_llm("question two", system="X" + prefix)
    assert first["cached_tokens"] == 0 and again["cached_tokens"] >= 1024 and changed["cached_tokens"] == 0
    assert cost(2000, 0, "mock-model", 1000) < cost(2000, 0, "mock-model")
    assert again["ttft_kind"] == "simulated first byte"
    assert call_llm("q", stream=True)["ttft_kind"] == "simulated stream"
