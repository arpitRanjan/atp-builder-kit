# (b) Every notebook runs top to bottom offline with no errors.
import json
import os

import nbformat
import pytest
from nbclient import NotebookClient

from conftest import ROOT

NOTEBOOKS = sorted((ROOT / "notebooks").glob("*.ipynb"))


def run_notebook(path, output_dir):
    nb = nbformat.read(path, as_version=4)
    os.environ["KIT_OUTPUT_DIR"] = str(output_dir)
    NotebookClient(nb, timeout=300, kernel_name="python3", resources={"metadata": {"path": str(path.parent)}}).execute()
    return nb


@pytest.mark.parametrize("path", NOTEBOOKS, ids=[p.name for p in NOTEBOOKS])
def test_notebook_runs(path, tmp_path):
    run_notebook(path, tmp_path)


def test_traces_notebook_writes_backlog(tmp_path):
    run_notebook(ROOT / "notebooks" / "02_traces_pandas.ipynb", tmp_path)
    header = (tmp_path / "failure_backlog.csv").read_text().splitlines()[0]
    for col in ["trace_id", "segment", "layer_guess", "severity"]:
        assert col in header


def test_harness_writes_one_log_line_per_step(tmp_path):
    run_notebook(ROOT / "notebooks" / "06_harness.ipynb", tmp_path)
    lines = (tmp_path / "traces" / "run.jsonl").read_text().splitlines()
    assert lines and all({"input", "decision", "output", "latency_s"} <= set(json.loads(x)) for x in lines)


def test_tracing_notebook_writes_every_span_kind(tmp_path):
    run_notebook(ROOT / "notebooks" / "10_tracing.ipynb", tmp_path)
    spans = [json.loads(x) for x in (tmp_path / "traces" / "spans.jsonl").read_text().splitlines()]
    assert {s["name"] for s in spans} == {"request", "retrieval", "model_call", "tool_call"}
    assert sum(s["name"] == "request" for s in spans) == 20
    assert all({"latency_ms", "input_tokens", "output_tokens", "cost_usd"} <= set(s) for s in spans)


def test_customer_notebook_fills_the_field_log(tmp_path):
    run_notebook(ROOT / "notebooks" / "11_customer_deployment.ipynb", tmp_path)
    import csv
    rows = list(csv.DictReader(open(tmp_path / "field_log.csv")))
    assert rows and list(rows[0]) == ["date", "issue", "workaround", "decision", "note"]
    assert {r["decision"] for r in rows} <= {"configure", "build", "drop"}


def test_injection_notebook_logs_a_blocked_call_and_keeps_corpus_clean(tmp_path):
    before = (ROOT / "corpus" / "qn-02.md").read_text()
    regression = (ROOT / "evals" / "regression.jsonl").read_text()
    run_notebook(ROOT / "notebooks" / "13_injection_and_redteam.ipynb", tmp_path)
    blocked = [json.loads(x) for x in (tmp_path / "blocked_calls.jsonl").read_text().splitlines()]
    assert blocked and blocked[0]["host"] == "evil.example"
    assert (ROOT / "corpus" / "qn-02.md").read_text() == before
    assert (ROOT / "evals" / "regression.jsonl").read_text() == regression  # adding the same attacks is a no-op
