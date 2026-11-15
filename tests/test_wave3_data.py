# Data and files for Chapters 10 to 15: the simulated customer, the Spanish set, probes, regression cases, Makefile.
import csv
import json
import subprocess

import pytest

from conftest import ROOT

from kit.rag import VectorIndex, HashEmbedder, chunk_pages, parse_corpus

NW = ROOT / "data" / "customer_northwind"
NW_ACCESS = {"student": ["student", "tutor", "admin"], "tutor": ["tutor", "admin"], "admin": ["admin"]}


def test_northwind_pages_and_template():
    pages = parse_corpus(NW / "pages")
    assert len(pages) == 10 and {p["visibility"] for p in pages} == {"student", "tutor", "admin"}
    assert "Northwind Learning" in (NW / "BRIEF.md").read_text()
    ids = {p["id"] for p in pages}
    for q in map(json.loads, open(NW / "questions.jsonl")):
        assert q["role"] in NW_ACCESS and set(q["page_ids"]) <= ids


def test_northwind_leak_test():
    pages = parse_corpus(NW / "pages")
    vis = {p["id"]: p["visibility"] for p in pages}
    index = VectorIndex(chunk_pages(pages, 120, 30, access=NW_ACCESS), HashEmbedder())
    probes = [q["question"] for q in map(json.loads, open(NW / "questions.jsonl"))] + ["tutor pay", "safeguarding"]
    seen = lambda role: {vis[c["page_id"]] for q in probes for c, _ in index.search(q, k=5, role=role)}
    assert seen("student") == {"student"} and "admin" not in seen("tutor") and "admin" in seen(None)


def test_spanish_golden_set():
    cases = [json.loads(line) for line in open(ROOT / "evals" / "golden_es.jsonl")]
    kinds = [c["kind"] for c in cases]
    assert kinds.count("translated") == 15 and kinds.count("degraded") == 5
    sources = {json.loads(line)["qid"] for line in open(ROOT / "corpus" / "questions.jsonl")}
    for c in cases:
        assert c["source_qid"] in sources and c["vars"]["cite_any"]
        assert all(isinstance(v, (str, int)) for v in c["vars"].values())
    labels = list(csv.DictReader(open(ROOT / "evals" / "labels_es.csv")))
    assert len(labels) == 10 and {r["human_label"] for r in labels} == {"pass", "fail"}


def test_probes_and_regression_cases():
    probes = [json.loads(line) for line in open(ROOT / "evals" / "guardrail_probes.jsonl")]
    assert {p["expect"] for p in probes} == {"answer", "refuse"} and len({p["id"] for p in probes}) == len(probes)
    cases = [json.loads(line) for line in open(ROOT / "evals" / "regression.jsonl")]
    assert len(cases) == 6 and len({c["id"] for c in cases}) == 6
    assert {c["check"] for c in cases} <= {"no_outside_draft", "no_prompt_leak", "no_admin_cite", "no_outside_fetch",
                                           "stops_in_budget"}


@pytest.mark.parametrize("target", ["evals", "traces"])
def test_makefile_targets(target):
    out = subprocess.run(["make", "-n", target], cwd=ROOT, capture_output=True, text=True, check=True).stdout
    assert {"evals": "evals/run_evals.py", "traces": "kit.tracing"}[target] in out


def test_templates_exist():
    for name in ["HANDOFF.md", "TAKEHOME.md"]:
        assert (ROOT / "templates" / name).read_text().startswith("# ")


def test_no_long_dashes_in_tracked_files():
    files = subprocess.run(["git", "ls-files"], cwd=ROOT, capture_output=True, text=True, check=True).stdout.split()
    for name in files:
        path = ROOT / name
        if path.suffix in {".md", ".py", ".ipynb", ".jsonl", ".csv", ".yaml", ".txt"} or name == "Makefile":
            text = path.read_text(errors="ignore")
            assert chr(0x2014) not in text and chr(0x2013) not in text, name  # no em or en dashes
