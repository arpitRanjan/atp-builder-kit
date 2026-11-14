"""Run the acceptance cases and compare the pass rate with a ship bar you set.

The local app logic:   python scripts/acceptance.py --bar 0.8
A deployed app:        python scripts/acceptance.py --bar 0.8 --url https://your-app.example/ask
The URL must take POST {"question": "..."} and reply with JSON {"text": "...", "cited": ["qn-01"]}.
Exit code 0 when the pass rate meets the bar, 1 when it does not. Add KIT_OFFLINE=1 for the mock model.
"""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
CASES = ROOT / "evals" / "acceptance.jsonl"


def ask_local(question):
    from app.app import answer
    r = answer(question)
    return {"text": r["text"], "cited": r["cited"]}


def ask_url(url, question):
    import requests
    resp = requests.post(url, json={"question": question}, timeout=60)
    resp.raise_for_status()
    return resp.json()


def check(case, reply):
    """Reasons the case failed. An empty list means it passed."""
    reasons = []
    cited, text = set(reply.get("cited", [])), reply.get("text", "").lower()
    if case.get("cite_any") and not cited & set(case["cite_any"]):
        reasons.append(f"cites none of {case['cite_any']}")
    leaked = sorted(cited & set(case.get("never_cite", [])))
    if leaked:
        reasons.append(f"cites forbidden pages {leaked}")
    if case.get("must_contain_any") and not any(w.lower() in text for w in case["must_contain_any"]):
        reasons.append(f"says none of {case['must_contain_any']}")
    for w in case.get("must_not_contain", []):
        if w.lower() in text:
            reasons.append(f"says '{w}'")
    return reasons


def run(cases, ask):
    rows = []
    for case in cases:
        try:
            reasons = check(case, ask(case["question"]))
        except Exception as e:  # a crash or a bad reply counts as a failed case, not a crashed run
            reasons = [f"error: {type(e).__name__}: {e}"]
        rows.append({"id": case["id"], "passed": not reasons, "reasons": reasons})
    return rows


def main(argv=None):
    parser = argparse.ArgumentParser(description="Acceptance cases against a ship bar.")
    parser.add_argument("--bar", type=float, required=True, help="ship bar as a pass rate from 0 to 1, like 0.8")
    parser.add_argument("--url", help="a deployed endpoint; leave out to test the local app logic")
    parser.add_argument("--cases", default=str(CASES))
    args = parser.parse_args(argv)
    if not 0 <= args.bar <= 1:
        parser.error("--bar must be between 0 and 1")
    cases = [json.loads(line) for line in open(args.cases) if line.strip()]
    ask = (lambda q: ask_url(args.url, q)) if args.url else ask_local
    rows = run(cases, ask)
    for r in rows:
        print(("pass" if r["passed"] else "FAIL"), r["id"], "; ".join(r["reasons"]))
    passed = sum(r["passed"] for r in rows)
    rate = passed / len(rows)
    ok = rate >= args.bar
    print(f"\nPass rate {rate:.0%} ({passed}/{len(rows)}), ship bar {args.bar:.0%}: {'SHIP' if ok else 'DO NOT SHIP'}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
