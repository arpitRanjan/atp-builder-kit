"""Stage 14: trace every golden case, so each known failure can link to its own trace.

Run:   python stage-14/trace_failures.py        (add KIT_OFFLINE=1 to use the mock model)
Traces the golden set (evals/golden.jsonl) and the Spanish cases (evals/golden_es.jsonl) through the app as is.
Writes stage-14/traces/spans.jsonl (one JSON line per span) and stage-14/traces/failing-cases.csv
(set, case, question, why it failed, trace_id). Copy the failures you care about into stage-14/known-failures.md.
"""
import argparse
import csv
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "evals"))

from gates import hard_failures  # noqa: E402
from kit.tracing import Tracer, traced_answer  # noqa: E402
from run_evals import load_cases  # noqa: E402


def main(argv=None):
    parser = argparse.ArgumentParser(description="Trace the golden set and list the failing cases with trace ids.")
    parser.add_argument("--out", default=str(HERE / "traces"))
    parser.add_argument("--sets", default="golden,es", help="which case files: golden, es, or both")
    args = parser.parse_args(argv)
    out = Path(args.out)
    spans = out / "spans.jsonl"
    spans.unlink(missing_ok=True)
    tracer = Tracer(spans)
    rows = []
    files = {"golden": ROOT / "evals" / "golden.jsonl", "es": ROOT / "evals" / "golden_es.jsonl"}
    cases = [(name, c) for name in args.sets.split(",") for c in load_cases(files[name])]
    for name, case in cases:
        r = traced_answer(case["vars"]["question"], tracer, stream=False)
        fails = hard_failures(case["vars"], r)
        rows.append({"set": name, "case": case["description"], "question": case["vars"]["question"],
                     "passed": not fails, "why": "; ".join(fails), "trace_id": r["trace_id"]})
    failing = [r for r in rows if not r["passed"]]
    with open(out / "failing-cases.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(failing)
    for r in failing:
        print(f"FAIL  {r['set']}  {r['case']}  trace {r['trace_id']}  {r['why']}")
    print(f"\n{len(rows) - len(failing)}/{len(rows)} passed. {len(tracer.written)} spans in {spans}, "
          f"{len(failing)} failing cases in {out / 'failing-cases.csv'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
