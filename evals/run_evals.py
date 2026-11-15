"""Run the golden set through the app's answer function and apply the graders, with no npm needed.

Run:      python evals/run_evals.py          (add KIT_OFFLINE=1 to use the mock model)
Options:  --split dev|held-out|regression    only that part of the golden set
          --save                             write the run record to evals/runs/<run id>.json
          --check-prompts                    every prompt in prompts/ must name a passing eval run
                                             in prompts/APPROVALS.md (see stage-08/README.md)
Exit code 1 when a hard gate fails (or the judge fails with JUDGE_HARD=1), so CI can block the pull request.
The same graders run in promptfoo:  npx promptfoo@0.125.1 eval -c evals/promptfooconfig.yaml
"""
import argparse
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
                     "judge_reason": reason, "cited": result.get("cited", [])})
    return rows


def app_ask(question):
    from app.app import answer
    r = answer(question)
    return {"text": r["text"], "cited": r["cited"]}


def failed(row):
    return bool(row["hard"]) or (judge_is_hard() and row["judge"] in ("fail", "unparsed"))


def prompt_in_use():
    try:
        from app.app import PROMPT_FILE
        return Path(PROMPT_FILE)
    except ImportError:
        return None


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def record(rows):
    """The run record: what ran, on which prompt, and what passed. --save writes it to evals/runs/."""
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
            "passed": not any(failed(r) for r in rows), "by_split": by_split,
            "failed_cases": {r["case"]: r["hard"] for r in rows if r["hard"]}}


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
            problems.append(f"{p.name}: no row in prompts/APPROVALS.md")
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
    args = ap.parse_args(argv)

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
    rec = record(rows)
    print("Run id:", rec["run_id"], "| prompt:", rec["prompt_file"], "| passed:", rec["passed"])
    if args.save:
        RUNS.mkdir(parents=True, exist_ok=True)
        (RUNS / f"{rec['run_id']}.json").write_text(json.dumps(rec, indent=1) + "\n")
        print(f"Saved evals/runs/{rec['run_id']}.json. Name it in prompts/APPROVALS.md to approve the prompt.")
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
