# Stages 11 to 15: the notebooks, scripts and templates write what each stage brief asks for.
import csv
import json
import subprocess
import sys

import pytest

from conftest import ROOT
from test_notebooks import run_notebook


@pytest.fixture(scope="module")
def out11(tmp_path_factory):
    out = tmp_path_factory.mktemp("s11")
    run_notebook(ROOT / "notebooks" / "11_customer_deployment.ipynb", out)
    return out


@pytest.fixture(scope="module")
def out12(tmp_path_factory):
    out = tmp_path_factory.mktemp("s12")
    run_notebook(ROOT / "notebooks" / "12_locale_eval.ipynb", out)
    return out


@pytest.fixture(scope="module")
def out13(tmp_path_factory):
    out = tmp_path_factory.mktemp("s13")
    run_notebook(ROOT / "notebooks" / "13_guardrails.ipynb", out)
    run_notebook(ROOT / "notebooks" / "13_injection_and_redteam.ipynb", out)
    return out


def test_stage11_field_log_has_tags_roles_and_a_recurring_item(out11):
    rows = list(csv.DictReader(open(out11 / "field-log.csv")))
    assert list(rows[0]) == ["date", "item", "issue", "workaround", "decision", "role_or_surface", "note"]
    assert {r["decision"] for r in rows} <= {"configure", "build", "drop"} and all(r["role_or_surface"] for r in rows)
    items = [r["item"] for r in rows]
    assert max(items.count(i) for i in items) >= 2


def test_stage11_leak_test_per_role_with_raw_links(out11):
    summary = list(csv.DictReader(open(out11 / "leak-test" / "summary.csv")))
    assert [r["role"] for r in summary] == ["student", "tutor", "admin"]
    for r in summary:
        assert int(r["prompts_run"]) == int(r["passed"]) + int(r["failed"]) and r["failed"] == "0"
        assert (out11 / "leak-test" / f"raw-{r['role']}.jsonl").exists()
    md = (out11 / "leak-test" / "summary.md").read_text()
    assert "| Role | Prompts run | Passed | Failed | Raw output |" in md and "raw-control-no-filter.jsonl" in md


def test_stage11_audit_log_keeps_no_raw_text_and_change_has_before_after(out11):
    lines = [json.loads(x) for x in (out11 / "audit-log.jsonl").read_text().splitlines()]
    assert lines and all({"time", "action", "role", "qid", "provider", "model"} <= set(x) for x in lines)
    assert not any("question" in x or "answer" in x or "text" in x for x in lines)
    ev = list(csv.DictReader(open(out11 / "change-evidence.csv")))
    assert ev and {"before_has_support_line", "after_has_support_line"} <= set(ev[0])
    assert (out11 / "answers.jsonl").exists()


def test_stage12_golden_set_outputs_ci_and_judge(out12):
    cases = [json.loads(x) for x in (out12 / "golden-set.jsonl").read_text().splitlines()]
    assert len(cases) >= 10 and all(c["input"] and c["expected"] and c["source"] for c in cases)
    kinds = {c["degradation"] for c in cases}
    assert "mixed_language" in kinds and any("typo" in k for k in kinds)
    outputs = [json.loads(x) for x in (out12 / "outputs.jsonl").read_text().splitlines()]
    assert {o["setup"] for o in outputs} == {"as is", "variant"} and all("output" in o for o in outputs)
    ci = json.loads((out12 / "results" / "ci-results.json").read_text())
    assert ci["cases"] == len(cases) and 0 <= ci["pass_rate"] <= 1 and ci["gate"] in {"pass", "fail"}
    assert "PASS only if" in (out12 / "judge-prompt.md").read_text()
    agreement = (out12 / "judge-agreement.md").read_text()
    assert "Agreement:" in agreement and "%" in agreement and "| id |" in agreement
    assert len(list(csv.DictReader(open(out12 / "judge-agreement.csv")))) >= 10


def test_stage12_ci_runner_exits_on_the_bar(tmp_path):
    env = {"KIT_OFFLINE": "1", "PATH": "/usr/bin:/bin"}
    ok = subprocess.run([sys.executable, str(ROOT / "stage-12" / "locale_evals.py"), "--out", str(tmp_path / "r.json")],
                        cwd=ROOT, env=env, capture_output=True, text=True)
    assert ok.returncode == 0, ok.stdout + ok.stderr
    high = subprocess.run([sys.executable, str(ROOT / "stage-12" / "locale_evals.py"), "--bar", "1.01",
                           "--out", str(tmp_path / "r2.json")], cwd=ROOT, env=env, capture_output=True, text=True)
    assert high.returncode == 1


def test_stage13_saves_evidence_for_every_requirement(out13):
    g = json.loads((out13 / "guardrail-summary.json").read_text())
    assert {"false_refusal_rate", "added_latency_p50_s", "output_check", "rate_limit", "spend_cap"} <= set(g)
    assert "rate_limited" in g["rate_limit"]["user_a"] and g["output_check"]["status"] == "refused_output"
    assert (out13 / "guardrail-runs.csv").exists() and (out13 / "blocked_calls.jsonl").read_text().strip()
    assert "Support process" in (out13 / "injected-docs" / "qn-02.md").read_text()
    runs = list(csv.DictReader(open(out13 / "injection-runs.csv")))
    assert [r["setup"] for r in runs].count("no defense") == 5 and [r["setup"] for r in runs].count("approval in code") == 5
    outcomes = list(csv.DictReader(open(out13 / "redteam-outcomes.csv")))
    assert len(outcomes) >= 6 and {"no defense", "defended", "passes_all_3_defended"} <= set(outcomes[0])
    rt = json.loads((out13 / "redteam-summary.json").read_text())
    assert rt["k"] == 3 and 0 <= rt["pass_k_defended"] <= 1 and rt["worst_attack"]
    fb = json.loads((out13 / "fallback.json").read_text())
    assert {"primary", "fallback", "gap", "routing_rule", "degraded_message"} <= set(fb) and fb["degraded_message"]
    table = (out13 / "authority-table.md").read_text()
    assert "| Tool | Authority | Reversibility | Who approves | Worst likely mistake" in table
    for tool in ["search_docs", "draft_issue", "fetch_url"]:
        assert f"| {tool} |" in table
    assert not (out13 / "corpus_injected").exists()


def test_stage14_trace_failures_writes_spans_and_failing_cases(tmp_path):
    env = {"KIT_OFFLINE": "1", "PATH": "/usr/bin:/bin"}
    r = subprocess.run([sys.executable, str(ROOT / "stage-14" / "trace_failures.py"), "--out", str(tmp_path)],
                       cwd=ROOT, env=env, capture_output=True, text=True)
    assert r.returncode == 0, r.stdout + r.stderr
    spans = [json.loads(x) for x in (tmp_path / "spans.jsonl").read_text().splitlines()]
    ids = {s["trace_id"] for s in spans}
    failing = list(csv.DictReader(open(tmp_path / "failing-cases.csv")))
    assert all(f["trace_id"] in ids for f in failing)


@pytest.mark.parametrize("stage,names", [
    ("11", ["notebooks/11_customer_deployment.ipynb", "leak-test/", "field-log.csv", "procurement-pack.md",
            "Decisions, Measures, and Next", "commit hash"]),
    ("12", ["golden-set.jsonl", "judge-prompt.md", "judge-agreement.md", "ci-results.json", "ship with a named limit"]),
    ("13", ["Decisions and results", "pass^3", "blocked_calls.jsonl", "authority-table.md", "fallback.json",
            "evals/regression.jsonl"]),
    ("14", ["SPEC.md", "known-failures.md", "peer-run-notes.md", "make evals", "Decisions, what I measured, and next",
            "traces/spans.jsonl"]),
    ("15", ["TAKEHOME.md", "PORTFOLIO_README.md", "25 to 35 minute", "Live", "What the results mean"]),
])
def test_stage_readmes_name_the_brief_files(stage, names):
    text = (ROOT / f"stage-{stage}" / "README.md").read_text()
    for name in names:
        assert name in text, name
    for old in ["DEPLOYMENT.md", "SOLUTION.md", "LOCALE.md", "field_log.csv", "HANDOFF.md` and"]:
        assert old not in text, old


def test_templates_for_the_late_stages():
    for name, words in {"HANDOFF.md": ["Decisions, what I measured, and next", "make evals"],
                        "SPEC.md": ["In scope", "Out of scope", "human approval"],
                        "KNOWN_FAILURES.md": ["User impact", "Trace"],
                        "PEER_RUN_NOTES.md": ["Date", "Who", "finish", "README"],
                        "TAKEHOME.md": ["small feature", "repo area", "eval gate", "Ship or no ship", "Pull request"],
                        "PORTFOLIO_README.md": ["Live app", "Who it is for", "How quality is checked", "Current limits",
                                                "badge.svg"],
                        "PROCUREMENT_PACK.md": ["leak test", "retention", "audit log", "data terms", "AI disclosure"]}.items():
        text = (ROOT / "templates" / name).read_text()
        assert text.startswith("# ")
        for w in words:
            assert w in text, (name, w)
