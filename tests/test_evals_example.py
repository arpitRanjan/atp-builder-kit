# The eval logic behind evals/promptfooconfig.yaml and evals/run_evals.py, tested offline.
import json
import sys

from conftest import ROOT

sys.path.insert(0, str(ROOT / "evals"))
import gates  # noqa: E402
import run_evals  # noqa: E402

CASE = {"question": "q", "cite_any": "qn-02", "never_cite": "qn-13,qn-14,qn-15", "max_words": 10}


def test_golden_set_shape():
    cases = run_evals.load_cases()
    assert len(cases) == 20
    for c in cases:
        assert c["vars"]["question"] and gates.as_list(c["vars"]["cite_any"])
        assert all(isinstance(v, (str, int)) for v in c["vars"].values())  # lists would multiply promptfoo tests


def test_hard_gates():
    assert gates.hard_failures(CASE, {"text": "Choose Export.", "cited": ["qn-02"]}) == []
    assert gates.hard_failures(CASE, {"text": "Choose Export.", "cited": ["qn-05"]}) == ["cites none of ['qn-02']"]
    assert "cites forbidden pages ['qn-13']" in gates.hard_failures(CASE, {"text": "ok", "cited": ["qn-02", "qn-13"]})
    assert gates.hard_failures(CASE, {"text": "I am not sure.", "cited": ["qn-02"]}) == ["empty or unsure answer"]


def test_advisory_never_fails():
    long = {"text": "word " * 50, "cited": ["qn-02", "qn-03", "qn-04"]}
    result = gates.advisory_gate(json.dumps(long), {"vars": CASE})
    assert result["pass"] is True and result["score"] == 0.0 and "over 10" in result["reason"]
    assert gates.hard_gate(json.dumps(long), {"vars": CASE})["pass"] is True


def test_runner_on_the_app_offline():
    rows = run_evals.run(run_evals.load_cases(), run_evals.app_ask)
    assert len(rows) == 20 and all(set(r) == {"case", "hard", "advisory"} for r in rows)
    assert any(not r["hard"] for r in rows)


def test_promptfoo_provider_offline():
    import promptfoo_provider
    out = json.loads(promptfoo_provider.call_api("How do I export a note as PDF?", {}, {})["output"])
    assert "qn-02" in out["cited"] and gates.hard_gate(json.dumps(out), {"vars": CASE})["pass"]


def test_workflow_template_is_disabled_in_the_kit():
    workflows = ROOT / ".github" / "workflows"
    assert (workflows / "evals.yml.example").exists()
    # A fork turns it on at Stage 8 (and saves a run); so does an example branch (it has an EXAMPLE.md).
    if not any(ROOT.glob("stage-*/EXAMPLE.md")) and not any((ROOT / "evals" / "runs").glob("*.json")):
        assert not (workflows / "evals.yml").exists()
    assert "promptfooconfig.yaml" in (workflows / "evals.yml.example").read_text()
