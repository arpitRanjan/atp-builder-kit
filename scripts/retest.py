"""Stage 3 re-test: run 10 inputs 5 times each (50 runs) for the one failure you fixed, and save the results.

Local app logic:  python scripts/retest.py --inputs stage-03/evals/retest_inputs.jsonl
Live app:         python scripts/retest.py --inputs stage-03/evals/retest_inputs.jsonl --url https://your-app.onrender.com
Writes stage-03/evals/retest_results.csv (one row per run) and stage-03/evals/retest_summary.md
(the pass rule, the Stage 2 backlog item, the pass count and pass rate). Add KIT_OFFLINE=1 for the mock model.

The inputs file has one JSON object per line: id, question, and the same pass checks as
scripts/acceptance.py (cite_any, never_cite, must_contain_any, must_not_contain, expect_fallback).
Put two more keys on the FIRST line: "backlog_item" (which failure_backlog.csv row you fixed) and
"pass_rule" (the rule in plain words, written before you run).
"""
import argparse
import csv
import datetime as dt
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from acceptance import ask_local, ask_url, check  # noqa: E402

DEFAULT_OUT = ROOT / "stage-03" / "evals"


def retest(inputs, ask, runs=5):
    rows = []
    for case in inputs:
        for run in range(1, runs + 1):
            try:
                reply = ask(case["question"])
                reasons = check(case, reply)
            except Exception as e:  # a failed call counts as a failed run
                reply, reasons = {}, [f"error: {type(e).__name__}: {e}"]
            rows.append({"input_id": case["id"], "run": run, "question": case["question"],
                         "passed": not reasons, "reasons": "; ".join(reasons),
                         "cited": " ".join(reply.get("cited") or []), "fallback": reply.get("fallback") or "",
                         "model": reply.get("model") or "", "answer": (reply.get("text") or "")[:200]})
    return rows


def main(argv=None):
    parser = argparse.ArgumentParser(description="Re-test one fixed failure: 10 inputs x 5 runs.")
    parser.add_argument("--inputs", required=True, help="JSONL file with your 10 inputs and their pass checks")
    parser.add_argument("--runs", type=int, default=5)
    parser.add_argument("--url", help="a deployed endpoint (app/api.py); leave out to test the local app logic")
    parser.add_argument("--out-dir", default=str(DEFAULT_OUT))
    args = parser.parse_args(argv)
    inputs = [json.loads(line) for line in open(args.inputs) if line.strip()]
    if len(inputs) != 10 or args.runs != 5:
        print(f"Note: the brief asks for 10 inputs x 5 runs. You have {len(inputs)} x {args.runs}.")
    ask = (lambda q: ask_url(args.url, q)) if args.url else ask_local
    rows = retest(inputs, ask, args.runs)

    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    with open(out / "retest_results.csv", "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    passed = sum(r["passed"] for r in rows)
    first = inputs[0]
    lines = [
        "# Re-test of one fixed failure",
        "",
        f"- Date (UTC): {dt.datetime.now(dt.timezone.utc).strftime('%Y-%m-%d %H:%M')}",
        f"- Target: {args.url or 'local app logic (app/app.py answer())'}",
        f"- Model: {', '.join(sorted({r['model'] for r in rows if r['model']})) or 'not reported'}",
        f"- Stage 2 backlog item fixed: {first.get('backlog_item', '<say which failure_backlog.csv row>')}",
        f"- Pass rule: {first.get('pass_rule', '<write the pass rule before you run>')}",
        f"- Inputs: `{Path(args.inputs).name}` ({len(inputs)} inputs x {args.runs} runs = {len(rows)} runs)",
        f"- Results: `retest_results.csv`",
        "",
        f"**Passed {passed} of {len(rows)} runs ({passed / len(rows):.0%}).**",
        "",
        "| Input | Passed runs |",
        "| --- | --- |",
    ]
    for case in inputs:
        n = sum(r["passed"] for r in rows if r["input_id"] == case["id"])
        lines.append(f"| {case['id']}: {case['question']} | {n} of {args.runs} |")
    (out / "retest_summary.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    sys.exit(main())
