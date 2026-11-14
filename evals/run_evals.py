"""Run the golden set through the app's answer function and apply the gates, with no npm needed.

Run:      python evals/run_evals.py          (add KIT_OFFLINE=1 to use the mock model)
Exit code 1 when any hard gate fails, so CI can block the pull request. Advisory results only print.
The same gates run in promptfoo:  npx promptfoo@0.125.1 eval -c evals/promptfooconfig.yaml
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "evals"))

from gates import advisory_warnings, hard_failures  # noqa: E402

GOLDEN = ROOT / "evals" / "golden.jsonl"


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


def app_ask(question):
    from app.app import answer
    r = answer(question)
    return {"text": r["text"], "cited": r["cited"]}


def main():
    rows = run(load_cases(), app_ask)
    for r in rows:
        status = "FAIL" if r["hard"] else "pass"
        print(f"{status}  {r['case']}  {'; '.join(r['hard'])}  {('advisory: ' + '; '.join(r['advisory'])) if r['advisory'] else ''}")
    hard = sum(bool(r["hard"]) for r in rows)
    print(f"\nHard gates: {len(rows) - hard}/{len(rows)} passed. Advisory warnings: {sum(bool(r['advisory']) for r in rows)}.")
    return 1 if hard else 0


if __name__ == "__main__":
    sys.exit(main())
