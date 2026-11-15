# The beginner guide fixes: each step a learner is asked to do is possible with the kit as shipped.
import csv
import importlib.util
import json
import subprocess
import sys

import nbformat
import pytest
from nbclient import NotebookClient

from conftest import ROOT

sys.path.insert(0, str(ROOT / "evals"))
sys.path.insert(0, str(ROOT / "scripts"))
import acceptance  # noqa: E402
import run_evals  # noqa: E402

NB = ROOT / "notebooks"
WORKFLOW = ROOT / ".github" / "workflows" / "evals.yml.example"


def run_nb(name, out, monkeypatch, **env):
    monkeypatch.setenv("KIT_OUTPUT_DIR", str(out))
    for k, v in env.items():
        monkeypatch.setenv(k, str(v))
    nb = nbformat.read(NB / name, as_version=4)
    NotebookClient(nb, timeout=300, kernel_name="python3", resources={"metadata": {"path": str(NB)}}).execute()
    return nb


def outputs(nb):
    return "\n".join(o.get("text") or o.get("data", {}).get("text/plain", "")
                     for cell in nb.cells for o in cell.get("outputs", []))


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# 1. Stage 1 first calls answer over the help pages
def test_first_calls_put_the_help_pages_in_the_system_prompt(tmp_path, monkeypatch):
    nb = run_nb("01_first_calls.ipynb", tmp_path, monkeypatch)
    step3 = next(c.source for c in nb.cells if c.cell_type == "code" and "SYSTEM =" in c.source)
    for name in ["SYSTEM", "TEMPERATURE", "MAX_OUTPUT_TOKENS", "TRUNCATE_CAP", "MODEL", "QUESTIONS", "CAPS"]:
        assert f"{name} =" in step3
    assert "corpus" in step3 and "Answer only from the help pages" in step3 and "page id" in step3
    assert "12 help pages in the system prompt" in outputs(nb)  # public and team pages, never admin ones
    usage = list(csv.DictReader(open(tmp_path / "usage.csv")))
    assert len(usage) == 10 and all(2000 < int(r["input_tokens"]) < 6000 for r in usage)  # pages sent, kept small
    assert "MAX" in usage[-1]["stop_reason"].upper()  # call 10 still truncated


# 2. Stage 2 finds probe_runs.csv in more places and says which one it used
def test_traces_notebook_says_where_probe_runs_came_from(tmp_path, monkeypatch):
    empty = tmp_path / "empty"
    empty.mkdir()
    nb = run_nb("02_traces_pandas.ipynb", tmp_path / "out1", monkeypatch, KIT_STAGE1_DIR=empty)
    text = outputs(nb)
    assert "No Stage 1 probe_runs.csv found" in text and str(ROOT.parent) in text and str(ROOT / "stage-01") in text

    stage1 = tmp_path / "s1"
    stage1.mkdir()
    with open(stage1 / "probe_runs.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["probe_id", "model", "check_type", "run", "text", "passed"])
        w.writerow(["p01", "m1", "valid_json", 1, "not json", False])
        w.writerow(["p01", "m1", "valid_json", 2, "{}", True])
    nb = run_nb("02_traces_pandas.ipynb", tmp_path / "out2", monkeypatch, KIT_STAGE1_DIR=stage1)
    assert f"Using Stage 1 probe runs from: {stage1 / 'probe_runs.csv'}" in outputs(nb)


# 3. acceptance cases without an id
def test_acceptance_case_without_id_does_not_crash():
    rows = acceptance.run([{"question": "How do I export a note as PDF?"}, {"id": "x", "question": "zzzz"}],
                          lambda q: {"text": "ok", "cited": []})
    assert [r["id"] for r in rows] == ["case-01", "x"]


# 4. the folders the briefs write into exist on main
@pytest.mark.parametrize("folder", ["stage-06/traces", "stage-10/traces", "stage-11/notebooks", "stage-11/leak-test",
                                    "stage-12/results", "stage-13/injected-docs"])
def test_stage_folders_exist(folder):
    assert (ROOT / folder / ".gitkeep").exists()


# 5. the shipped prompts/APPROVALS.md passes --check-prompts on a fresh fork
def test_shipped_approvals_pass_and_only_for_the_kit_prompt(tmp_path):
    files, problems = run_evals.check_prompts()
    assert [p.name for p in files] == ["help_v1.md"] and problems == []
    assert "kit-baseline" in (ROOT / "prompts" / "APPROVALS.md").read_text()
    prompts = tmp_path / "prompts"
    prompts.mkdir()
    (prompts / "APPROVALS.md").write_bytes((ROOT / "prompts" / "APPROVALS.md").read_bytes())
    (prompts / "help_v1.md").write_text("A changed prompt.")
    problems = run_evals.check_prompts(prompts, tmp_path / "runs")[1]
    assert len(problems) == 1 and "kit-baseline" in problems[0] and "--save" in problems[0]


# 6. a pass bar, and a workflow a fresh fork can pass
def test_bar_sets_the_gate(tmp_path, monkeypatch):
    monkeypatch.setattr(run_evals, "RUNS", tmp_path / "runs")
    real = run_evals.app_ask
    bad = {"How do I export a note as PDF?", "How do I create a note and rename it?"}  # 2 of 20 fail
    monkeypatch.setattr(run_evals, "app_ask", lambda q: {"text": "", "cited": []} if q in bad else real(q))
    assert run_evals.main([]) == 1  # default bar: every case must pass
    assert run_evals.main(["--bar", "0.85", "--save"]) == 0  # 18 of 20 is over 85%
    assert run_evals.main(["--bar", "0.95"]) == 1
    rec = json.loads(next((tmp_path / "runs").glob("*.json")).read_text())
    assert rec["passed"] and rec["bar"] == 0.85 and rec["pass_rate"] == 0.9
    with pytest.raises(SystemExit):
        run_evals.main(["--bar", "85"])


def test_workflow_template_is_passable_as_shipped(tmp_path):
    import yaml
    flow = yaml.safe_load(WORKFLOW.read_text())
    triggers = flow[True] if True in flow else flow["on"]  # YAML 1.1 reads the key "on" as True
    assert "pull_request" in triggers and triggers["push"]["branches"] == ["main"]
    job = flow["jobs"]["golden-set"]
    bar = float(job["env"]["EVAL_BAR"])
    assert 0 < bar < 1 and int(job["env"]["PROMPTFOO_PASS_RATE_THRESHOLD"]) == round(bar * 100)
    steps = {s.get("name", ""): s for s in job["steps"]}
    golden = next(s for n, s in steps.items() if n.startswith("Golden set, pytest"))
    assert '--bar "$EVAL_BAR"' in golden["run"]
    retrieval = next(s for n, s in steps.items() if "Stage 9" in n)
    assert retrieval["env"]["KIT_OFFLINE"] == "1"
    spanish = next(s for n, s in steps.items() if "Stage 12" in n)
    assert not (ROOT / "stage-12" / "golden-set.jsonl").exists()  # a fresh fork has not done Stage 12
    out = subprocess.run(["bash", "-e", "-c", spanish["run"]], cwd=ROOT, capture_output=True, text=True)
    assert out.returncode == 0 and "Skipping the Spanish golden set" in out.stdout
    takehome = (ROOT / "templates" / "TAKEHOME.md").read_text()
    assert "17 of 20" in takehome and "--bar 0.85" in takehome and bar == 0.85


def test_retrieval_step_passes_offline_on_a_fresh_fork(tmp_path):
    out = subprocess.run([sys.executable, str(ROOT / "evals" / "retrieval_check.py"), "--out", str(tmp_path)],
                         cwd=ROOT, capture_output=True, text=True, env={"PATH": "/usr/bin:/bin", "KIT_OFFLINE": "1"})
    assert out.returncode == 0, out.stdout + out.stderr


# 7. a saved run keeps what a learner needs to hand label it
def test_saved_run_keeps_question_reference_and_answer(tmp_path, monkeypatch):
    monkeypatch.setattr(run_evals, "RUNS", tmp_path / "runs")
    assert run_evals.main(["--split", "dev", "--save"]) == 0
    rec = json.loads(next((tmp_path / "runs").glob("*.json")).read_text())
    assert {"run_id", "passed", "by_split", "failed_cases", "prompt_sha256"} <= set(rec)  # the old fields stay
    detail = rec["cases_detail"]
    assert len(detail) == rec["cases"] == 10
    golden = {c["description"]: c["vars"] for c in run_evals.load_cases()}
    for row in detail:
        assert row["question"] == golden[row["case"]]["question"]
        assert row["reference"] == golden[row["case"]]["reference"] and row["answer"]
        assert "label" in row


# 8. the Stage 7 oversight app
@pytest.fixture
def oversight(tmp_path, monkeypatch):
    from streamlit.testing.v1 import AppTest
    monkeypatch.setenv("STAGE07_LOG_DIR", str(tmp_path))
    return lambda: AppTest.from_file(str(ROOT / "stage-07" / "oversight_app.py"), default_timeout=60).run()


def test_oversight_clears_the_question_and_offers_the_outbox(oversight, tmp_path):
    from kit import approval
    at = oversight()
    at.text_input[0].set_value(approval.SUGGESTED_PROMPTS[2]).run()
    next(b for b in at.button if b.label == "Approve").click().run()
    assert at.success and "Approved" in at.success[0].value
    assert at.text_input[0].value == ""  # the box is empty, so it does not draft again
    assert [b.label for b in at.button] == approval.SUGGESTED_PROMPTS  # back at the empty state
    assert len((tmp_path / "outbox.jsonl").read_text().splitlines()) == 1
    assert "Download outbox.jsonl" in [b.label for b in at.sidebar.get("download_button")]
    at.text_input[0].set_value(approval.SUGGESTED_PROMPTS[2]).run()
    next(b for b in at.button if b.label == "Reject").click().run()
    assert at.text_input[0].value == "" and len((tmp_path / "outbox.jsonl").read_text().splitlines()) == 1


def test_oversight_feedback_attaches_to_the_shown_answer(oversight, tmp_path, monkeypatch):
    import app.app
    calls = []
    real = app.app.answer

    def changing_answer(question, *a, **k):  # like a live model: a new wording on every call
        calls.append(question)
        r = real(question, *a, **k)
        return dict(r, text=f"{r['text']} (wording {len(calls)})")

    monkeypatch.setattr(app.app, "answer", changing_answer)
    at = oversight()
    at.text_input[0].set_value("How do I export a note as PDF?").run()
    shown = next(c.value for c in at.caption if c.value.startswith("Answer id:"))
    next(b for b in at.button if b.label == "Thumbs down").click().run()
    assert calls == ["How do I export a note as PDF?"]  # no new model call on the rerun
    row = json.loads((tmp_path / "feedback.jsonl").read_text().splitlines()[0])
    assert shown == f"Answer id: {row['answer_id']}" and row["answer"].endswith("(wording 1)")


# 9. a real tool handler with the host allowlist, and the Stage 11 answer file
def test_app_fetch_url_blocks_and_logs_other_hosts(tmp_path, monkeypatch):
    from app import tools
    monkeypatch.setattr(tools.ALLOWLIST, "log_path", tmp_path / "blocked_calls.jsonl")
    assert tools.BLOCKED_LOG == ROOT / "stage-13" / "blocked_calls.jsonl"
    ok = tools.fetch_url("https://help.quillnote.example/qn-02")
    assert "PDF" in ok["text"]
    blocked = tools.fetch_url("https://evil.example/collect?q=sync")
    assert blocked["blocked"] and blocked["host"] == "evil.example"
    log = [json.loads(x) for x in (tmp_path / "blocked_calls.jsonl").read_text().splitlines()]
    assert len(log) == 1 and log[0]["tool"] == "fetch_url" and log[0]["host"] == "evil.example"
    assert "app/tools.py" in (ROOT / "stage-13" / "README.md").read_text()


class FakeIndex:
    def search(self, question, k=3, role=None):
        return [({"id": "nw-01#0", "page_id": "nw-01", "text": "Book a lesson from the calendar."}, 1.0)]


def test_stage11_answer_file_drives_the_notebook(monkeypatch):
    mod = load_module("stage11_answer_test", ROOT / "stage-11" / "answer.py")
    logged = []
    text, cited, retrieved = mod.answer("How do I book?", "student", FakeIndex(), audit=lambda *a: logged.append(a))
    assert retrieved == ["nw-01"] and len(logged) == 1
    monkeypatch.setattr(mod, "answer", lambda *a, **k: ("I do not know.", set(), ["nw-01"]))
    assert mod.answer_with_support("Gift card?", "student", FakeIndex())[0].endswith(mod.SUPPORT_LINE)
    nb = nbformat.read(NB / "11_customer_deployment.ipynb", as_version=4)
    code = "\n".join(c.source for c in nb.cells if c.cell_type == "code")
    assert 'ROOT / "stage-11" / "answer.py"' in code and "stage11.answer_with_support(" in code
    assert "SYSTEM = (" not in code and "SUPPORT_LINE = " not in code  # no second copy in the notebook


# 10. a light requirements file for Streamlit Cloud, and the MCP Inspector proxy port
def test_app_requirements_are_light_and_cover_the_app_imports():
    names = {line.split("==")[0].lower() for line in (ROOT / "app" / "requirements.txt").read_text().splitlines()
             if line.strip() and not line.startswith("#")}
    assert {"streamlit", "google-genai", "openai", "mcp"} <= names
    assert not names & {"torch", "sentence-transformers", "transformers", "pandas", "duckdb"}
    assert "app/requirements.txt" in (ROOT / "app" / "README.md").read_text()
    assert "6277" in (ROOT / ".devcontainer" / "devcontainer.json").read_text()


# 11. Stage 12: the CI step is kept, not added
def test_stage12_readme_says_the_ci_step_exists():
    text = (ROOT / "stage-12" / "README.md").read_text()
    assert "already has the Spanish step" in text and "do not need to add" in text
    assert "Stage 12" in WORKFLOW.read_text()


# 12. Stage 6 tasks carry their own pass checks
def test_harness_tasks_carry_expect_and_approval(tmp_path, monkeypatch):
    nb = nbformat.read(NB / "06_harness.ipynb", as_version=4)
    code = "\n".join(c.source for c in nb.cells if c.cell_type == "code")
    assert 't["id"] ==' not in code and 't["id"] in APPROVED' not in code and 'APPROVED = {"t06"}' not in code
    assert code.count('"expect":') == 10 and '"approved": True' in code and '"approved": False' in code
    nb = run_nb("06_harness.ipynb", tmp_path, monkeypatch)
    rows = list(csv.DictReader(open(tmp_path / "pass_rates.csv")))
    assert len(rows) == 7 and all(r["tasks"] == "10" for r in rows)
    assert {r["config"]: r for r in rows}["all on"]["passed"] == "10"
    assert len(list(csv.DictReader(open(tmp_path / "runs.csv")))) == 70
    assert (tmp_path / "failed_run.md").exists() and (tmp_path / "outbox.jsonl").exists()
