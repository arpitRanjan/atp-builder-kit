"""Run the golden set through the app's answer function and apply the graders, with no npm needed.

Run:      python evals/run_evals.py          (add KIT_OFFLINE=1 to use the mock model)
Options:  --split dev|held-out|regression    only that part of the golden set
          --save                             write the run record to evals/runs/<run id>.json, with every case's
                                             question, reference answer and the model's answer (for hand labels)
          --bar 0.85                         pass when at least this share of cases passes the hard gates
                                             (default: the EVAL_BAR environment variable, else 0.85, as in CI)
          --labels-out PATH                  write a CSV of every case (id, split, question, reference, answer,
                                             and an empty label column) to hand label for Stage 8
          --check-prompts                    every prompt in prompts/ must name a passing eval run
                                             in prompts/APPROVALS.md (see stage-08/README.md)
Exit code 1 when the pass rate is under the bar (a case fails on any hard gate, or on the judge with
JUDGE_HARD=1), so CI can block the pull request. --bar 1 makes every case count.
The same graders run in promptfoo:  npx promptfoo@0.125.1 eval -c evals/promptfooconfig.yaml
"""
import argparse
import csv
import hashlib
import json
import os
import re
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "evals"))

from gates import advisory_warnings, hard_failures, judge_is_hard, judge_verdict  # noqa: E402

GOLDEN = ROOT / "evals" / "golden.jsonl"
RUNS = ROOT / "evals" / "runs"
PROMPTS = ROOT / "prompts"
SPLITS = ("dev", "held-out", "regression")
DEFAULT_BAR = 0.85  # the same default as EVAL_BAR in .github/workflows/evals.yml.example and the Makefile
LABEL_COLUMNS = ["id", "split", "question", "reference", "answer", "label"]


def default_bar():
    return float(os.environ.get("EVAL_BAR") or DEFAULT_BAR)
# The kit's own baseline approval in prompts/APPROVALS.md. It approves the kit's help_v1.md text, unchanged, so
# --check-prompts passes on a fresh fork. It has no run file. Make a real run with --save and approve that instead.
# While help_v1.md is still the kit's text, it passes with no row at all, so replacing the row cannot break the check.
KIT_BASELINE = "kit-baseline"
KIT_BASELINE_PROMPTS = {"help_v1.md": "e9aaae95d6da02df6850c54c1f013bb383133e350e4bcb159d7ce183b89c6052"}


def load_cases(path=GOLDEN):
    return [json.loads(line) for line in open(path) if line.strip()]


def run(cases, ask):
    """ask(question) returns {"text": ..., "cited": [...]}. Returns one row per case."""
    rows = []
    for case in cases:
        result = ask(case["vars"]["question"])
        rows.append({"case": case["description"], "hard": hard_failures(case["vars"], result),
                     "advisory": advisory_warnings(case["vars"], result)})
    return rows


def run_full(cases, ask, judge=True):
    """Like run(), plus the split, the source and the model judge's verdict for every case."""
    rows = []
    for case in cases:
        result = ask(case["vars"]["question"])
        verdict, reason = judge_verdict(case["vars"], result) if judge else (None, "judge off")
        rows.append({"case": case["description"], "split": case["vars"].get("split", "dev"),
                     "source": case["vars"].get("source", ""), "hard": hard_failures(case["vars"], result),
                     "advisory": advisory_warnings(case["vars"], result), "judge": verdict,
                     "judge_reason": reason, "cited": result.get("cited", []),
                     "question": case["vars"]["question"], "reference": case["vars"].get("reference", ""),
                     "answer": result.get("text", "")})
    return rows


def app_ask(question):
    from app.app import answer
    r = answer(question)
    return {"text": r["text"], "cited": r["cited"]}


def failed(row):
    return bool(row["hard"]) or (judge_is_hard() and row["judge"] in ("fail", "unparsed"))


def pass_rate(rows):
    return sum(not failed(r) for r in rows) / len(rows) if rows else 0.0


def prompt_in_use():
    try:
        from app.app import PROMPT_FILE
        return Path(PROMPT_FILE)
    except ImportError:
        return None


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def record(rows, bar=None):
    """The run record: what ran, on which prompt, and what passed. --save writes it to evals/runs/.

    "passed" means the pass rate is at or above the bar. "cases_detail" keeps every case's question,
    reference answer and the model's answer, so you can hand label rows from a real run (Stage 8).
    """
    bar = default_bar() if bar is None else bar
    now = datetime.now(timezone.utc)
    prompt = prompt_in_use()
    digest = sha256(prompt) if prompt and prompt.exists() else ""
    from kit.llm import default_model, pick_provider
    provider = pick_provider()
    by_split = {}
    for split in SPLITS:
        part = [r for r in rows if r["split"] == split]
        if part:
            by_split[split] = {"cases": len(part), "hard_pass": sum(not r["hard"] for r in part),
                               "judge_pass": sum(r["judge"] == "pass" for r in part)}
    return {"run_id": now.strftime("%Y%m%dT%H%M%SZ") + (f"-{digest[:6]}" if digest else ""),
            "timestamp": now.isoformat(timespec="seconds"), "git_sha": os.environ.get("GITHUB_SHA", ""),
            "provider": provider, "model": default_model(provider),
            "prompt_file": prompt.relative_to(ROOT).as_posix() if prompt else None, "prompt_sha256": digest,
            "judge_hard": judge_is_hard(), "cases": len(rows), "hard_failures": sum(bool(r["hard"]) for r in rows),
            "judge_failures": sum(r["judge"] in ("fail", "unparsed") for r in rows),
            "pass_rate": round(pass_rate(rows), 4), "bar": bar, "passed": bool(rows) and pass_rate(rows) >= bar,
            "by_split": by_split, "failed_cases": {r["case"]: r["hard"] for r in rows if r["hard"]},
            "cases_detail": [{"case": r["case"], "split": r["split"], "question": r.get("question", ""),
                              "reference": r.get("reference", ""), "answer": r.get("answer", ""),
                              "cited": r["cited"], "hard": r["hard"], "advisory": r["advisory"],
                              "judge": r["judge"], "judge_reason": r["judge_reason"], "label": ""}
                             for r in rows]}


def write_labels(rec, path):
    """The run's cases as a CSV to hand label: fill the label column (pass or fail) yourself."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=LABEL_COLUMNS)
        w.writeheader()
        for c in rec["cases_detail"]:
            w.writerow({"id": c["case"], "split": c["split"], "question": c["question"],
                        "reference": c["reference"], "answer": c["answer"], "label": ""})
    return path


def check_prompts(prompts=PROMPTS, runs=RUNS):
    """Every prompt version must name, in prompts/APPROVALS.md, a saved passing run made on that exact text."""
    files = sorted(p for p in prompts.glob("*.md") if p.name not in ("README.md", "APPROVALS.md")) \
        if prompts.exists() else []
    table = (prompts / "APPROVALS.md").read_text() if (prompts / "APPROVALS.md").exists() else ""
    approved = dict(re.findall(r"^\|\s*`?([\w.-]+\.md)`?\s*\|\s*`?([\w-]+)`?\s*\|", table, re.M))
    problems = []
    for p in files:
        run_id = approved.get(p.name)
        rec = runs / f"{run_id}.json"
        if not run_id:
            if KIT_BASELINE_PROMPTS.get(p.name) != sha256(p):  # the kit's own unchanged prompt needs no row
                problems.append(f"{p.name}: no row in prompts/APPROVALS.md")
        elif run_id == KIT_BASELINE:
            if KIT_BASELINE_PROMPTS.get(p.name) != sha256(p):
                problems.append(f"{p.name}: the {KIT_BASELINE} row only approves the kit's own unchanged prompt "
                                f"text. Run python evals/run_evals.py --save and approve that run")
        elif not rec.exists():
            problems.append(f"{p.name}: eval run {run_id} has no file in evals/runs/")
        else:
            data = json.loads(rec.read_text())
            if not data.get("passed"):
                problems.append(f"{p.name}: eval run {run_id} did not pass")
            elif data.get("prompt_sha256") != sha256(p):
                problems.append(f"{p.name}: eval run {run_id} was made on different prompt text")
    return files, problems


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--split", choices=SPLITS)
    ap.add_argument("--save", action="store_true", help="write the run record to evals/runs/<run id>.json")
    ap.add_argument("--check-prompts", action="store_true", help="also check prompts/APPROVALS.md")
    ap.add_argument("--bar", type=float, default=None,
                    help="pass when this share of cases (0 to 1) passes the hard gates. Default: EVAL_BAR, else 0.85")
    ap.add_argument("--labels-out", help="also write the cases to this CSV to hand label, like evals/to_label.csv")
    args = ap.parse_args(argv)
    if args.bar is None:
        args.bar = default_bar()
    if not 0 <= args.bar <= 1:
        ap.error("--bar must be between 0 and 1")

    cases = [c for c in load_cases() if not args.split or c["vars"].get("split", "dev") == args.split]
    rows = run_full(cases, app_ask)
    for r in rows:
        status = "FAIL" if failed(r) else "pass"
        extra = f"  advisory: {'; '.join(r['advisory'])}" if r["advisory"] else ""
        print(f"{status}  {r['case']}  [{r['split']}]  judge {r['judge']}  {'; '.join(r['hard'])}{extra}")
    print()
    for split, n in Counter(r["split"] for r in rows).items():
        part = [r for r in rows if r["split"] == split]
        print(f"{split:10} hard gates {sum(not r['hard'] for r in part)}/{n} passed, "
              f"judge {sum(r['judge'] == 'pass' for r in part)}/{n} pass")
    hard = sum(bool(r["hard"]) for r in rows)
    print(f"\nHard gates: {len(rows) - hard}/{len(rows)} passed. Advisory warnings: {sum(bool(r['advisory']) for r in rows)}."
          f" Judge: {'hard' if judge_is_hard() else 'advisory'} (set JUDGE_HARD=1 to make it block).")
    rec = record(rows, args.bar)
    print(f"Pass rate {rec['pass_rate']:.0%}, bar {args.bar:.0%}.",
          "Run id:", rec["run_id"], "| prompt:", rec["prompt_file"], "| passed:", rec["passed"])
    if args.save:
        RUNS.mkdir(parents=True, exist_ok=True)
        (RUNS / f"{rec['run_id']}.json").write_text(json.dumps(rec, indent=1) + "\n")
        print(f"Saved evals/runs/{rec['run_id']}.json. Name it in prompts/APPROVALS.md to approve the prompt.")
    if args.labels_out:
        print(f"Wrote {len(rows)} cases to {write_labels(rec, args.labels_out)}. Fill the label column by hand.")
    bad = not rec["passed"]
    if args.check_prompts:
        files, problems = check_prompts()
        print(f"\nPrompt approvals: {len(files) - len(problems)}/{len(files)} prompt files name a passing run.")
        for p in problems:
            print("  FAIL", p)
        bad = bad or bool(problems)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
