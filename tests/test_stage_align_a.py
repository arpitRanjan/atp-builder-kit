# Stages 1 to 5: the notebooks and scripts write what each stage brief asks for.
import csv
import json
import socket
import sys
import threading
import time

import nbformat
import pytest
from nbclient import NotebookClient

from conftest import ROOT

sys.path.insert(0, str(ROOT / "scripts"))
import acceptance  # noqa: E402
import retest  # noqa: E402


def run_nb(name, out, monkeypatch, **env):
    monkeypatch.setenv("KIT_OUTPUT_DIR", str(out))
    for k, v in env.items():
        monkeypatch.setenv(k, str(v))
    path = ROOT / "notebooks" / name
    nb = nbformat.read(path, as_version=4)
    NotebookClient(nb, timeout=300, kernel_name="python3", resources={"metadata": {"path": str(path.parent)}}).execute()
    return nb


def outputs(nb):
    text = []
    for cell in nb.cells:
        for o in cell.get("outputs", []):
            text.append(o.get("text") or o.get("data", {}).get("text/plain", ""))
    return "\n".join(text)


def rows(path):
    return list(csv.DictReader(open(path)))


@pytest.fixture(scope="module")
def stage1(tmp_path_factory):
    out = tmp_path_factory.mktemp("stage1")
    mp = pytest.MonkeyPatch()
    try:
        run_nb("01_probe_set.ipynb", out, mp)
    finally:
        mp.undo()
    return out


# ---------- Stage 1 ----------
def test_first_calls_usage_table_has_10_rows_and_a_truncation(tmp_path, monkeypatch):
    run_nb("01_first_calls.ipynb", tmp_path, monkeypatch)
    usage = rows(tmp_path / "usage.csv")
    assert len(usage) == 10
    assert {"input_tokens", "output_tokens", "stop_reason", "latency_s", "cost_usd"} <= set(usage[0])
    assert any("MAX" in r["stop_reason"].upper() for r in usage)


def test_probe_set_runs_10_tasks_5_times_on_2_models(stage1):
    runs = rows(stage1 / "probe_runs.csv")
    assert len(runs) == 100 and len({r["model"] for r in runs}) == 2 and len({r["probe_id"] for r in runs}) == 10
    summary = rows(stage1 / "probe_summary.csv")
    assert len(summary) == 2 and {"pass_rate", "cost_per_task", "median_latency_s"} <= set(summary[0])


# ---------- Stage 2 ----------
def test_traces_notebook_meets_the_stage_2_brief(tmp_path, monkeypatch, stage1):
    nb = run_nb("02_traces_pandas.ipynb", tmp_path, monkeypatch, KIT_STAGE1_DIR=stage1)
    text = outputs(nb)
    assert "numerator" in text and "denominator" in text and "missed" in text
    for name in ["labeled_random_30.csv", "labeled_stratified_30.csv"]:
        sample = rows(tmp_path / name)
        assert len(sample) == 30 and all(r["failure_label"] for r in sample)
        assert "user_message" not in sample[0]
    assert not (tmp_path / "labeling_sample.csv").exists()
    backlog = rows(tmp_path / "failure_backlog.csv")
    for col in ["trace_ids", "failure_label", "layer_guess", "severity", "how_to_check_fix", "from_stage1_probe"]:
        assert col in backlog[0]
    assert {r["from_stage1_probe"] for r in backlog} == {"yes", "no"}
    assert all(r["layer_guess"] and r["severity"] and r["how_to_check_fix"] for r in backlog)
    # Nothing written to the stage folder may hold planted PII.
    planted = [v for line in open(ROOT / "data" / "traces.jsonl") for v in json.loads(line)["pii_planted"]]
    for f in tmp_path.glob("*.csv"):
        body = f.read_text()
        assert not [v for v in planted if v in body], f"PII in {f.name}"
    # The notebook is committed with its outputs, so its outputs may not show raw PII either.
    saved = nbformat.writes(nb)
    assert not [v for v in planted if v in saved], "PII in the traces notebook outputs"


def test_duckdb_trap_shows_wrong_then_corrected(tmp_path, monkeypatch):
    nb = run_nb("02_sql_duckdb.ipynb", tmp_path, monkeypatch)
    text = outputs(nb)
    assert text.index("Wrong:") < text.index("Corrected:")
    assert any("What caused the mistake" in c.source for c in nb.cells if c.cell_type == "markdown")


# ---------- Stage 3 ----------
def test_app_reads_the_versioned_prompt_file():
    from app import app
    assert app.PROMPT_FILE.parent.name == "prompts" and app.SYSTEM == app.PROMPT_FILE.read_text().strip()


def test_retest_writes_50_runs_and_the_fix_passes(tmp_path, monkeypatch):
    inputs = ROOT / "stage-03" / "evals" / "retest_inputs.example.jsonl"
    retest.main(["--inputs", str(inputs), "--out-dir", str(tmp_path / "before")])
    before = rows(tmp_path / "before" / "retest_results.csv")
    assert len(before) == 50
    from app import app
    monkeypatch.setattr(app, "HIDE_VISIBILITY", ["admin"])
    retest.main(["--inputs", str(inputs), "--out-dir", str(tmp_path / "after")])
    after = rows(tmp_path / "after" / "retest_results.csv")
    assert sum(r["passed"] == "True" for r in after) == 50 > sum(r["passed"] == "True" for r in before)
    summary = (tmp_path / "after" / "retest_summary.md").read_text()
    assert "Passed 50 of 50" in summary and "Pass rule" in summary and "backlog item" in summary


def test_mcp_describe_lists_the_tool_and_pinned_version():
    from mcp_server.describe import describe
    text = describe()
    assert "search_docs" in text and "mcp==" in text and "read_only_hint" in text


# ---------- Stage 4 ----------
def test_baseline_notebook_writes_two_case_files_a_comparison_and_a_choice(tmp_path, monkeypatch, stage1):
    run_nb("04_baseline_vs_llm.ipynb", tmp_path, monkeypatch, KIT_STAGE1_DIR=stage1)
    llm, base = rows(tmp_path / "llm_results.csv"), rows(tmp_path / "baseline_results.csv")
    assert len(llm) >= 20 and [r["case_id"] for r in llm] == [r["case_id"] for r in base]
    for col in ["case_id", "input", "expected", "pass_rule", "system_output", "passed", "latency_s", "cost_usd"]:
        assert col in llm[0] and col in base[0]
    assert len(rows(tmp_path / "comparison.csv")) == 2
    assert "avg_latency_s" in (tmp_path / "comparison.md").read_text()
    choice = (tmp_path / "stack_choice.md").read_text()
    assert choice.count("+ kit harness") >= 4 and "Data terms notes" in choice and "probe_summary.csv" in choice


# ---------- Stage 5 ----------
def test_acceptance_cases_mix_kinds():
    cases = [json.loads(line) for line in open(ROOT / "evals" / "acceptance.jsonl")]
    assert len(cases) >= 15 and {c["kind"] for c in cases} == {"normal", "edge", "failure"}


def test_app_fallbacks(monkeypatch):
    from app import app
    from kit.llm import LLMError
    assert app.answer("zzzz qqqq")["fallback"] == "no_page"
    assert app.answer("How do I export a note as PDF?")["fallback"] is None

    def boom(*a, **k):
        raise LLMError(503, "down")
    monkeypatch.setattr(app, "call_llm", boom)
    assert app.answer("How do I export a note as PDF?")["fallback"] == "model_error"


def test_expect_fallback_check():
    assert acceptance.check({"expect_fallback": "no_page"}, {"text": "x", "fallback": "no_page"}) == []
    assert acceptance.check({"expect_fallback": True}, {"text": "x", "fallback": None})
    assert acceptance.check({"expect_fallback": "no_page"}, {"text": "x", "fallback": "model_error"})


def test_api_endpoint_and_spend_guard(monkeypatch):
    pytest.importorskip("fastapi")
    pytest.importorskip("httpx")
    from fastapi.testclient import TestClient
    from app import api
    monkeypatch.setattr(api, "MAX_CALLS_PER_CLIENT", 2)
    api._counts.update(day=None)
    client = TestClient(api.app)
    r = client.post("/ask", json={"question": "How do I export a note as PDF?"}).json()
    assert "qn-02" in r["cited"] and r["fallback"] is None and r["model"]
    assert client.post("/ask", json={"question": "zzzz qqqq"}).json()["fallback"] == "no_page"
    blocked = client.post("/ask", json={"question": "How do I fix sync?"})
    assert blocked.status_code == 429 and blocked.json()["fallback"] == "spend_guard"
    assert "question" in client.get("/").text.lower()


def test_acceptance_against_the_live_api_saves_a_report(tmp_path):
    pytest.importorskip("fastapi")
    import uvicorn
    from app import api
    api._counts.update(day=None)
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        port = s.getsockname()[1]
    server = uvicorn.Server(uvicorn.Config(api.app, host="127.0.0.1", port=port, log_level="error"))
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()
    for _ in range(100):
        if server.started:
            break
        time.sleep(0.05)
    out = tmp_path / "acceptance-run.txt"
    try:
        code = acceptance.main(["--bar", "0.8", "--url", f"http://127.0.0.1:{port}", "--out", str(out)])
    finally:
        server.should_exit = True
        thread.join(5)
    report = out.read_text()
    assert code == 0
    assert f"Target: http://127.0.0.1:{port}" in report and "Date (UTC):" in report and "Model: mock-model" in report
    assert "pass a15 [failure]" in report and "Ship bar: 80%" in report
