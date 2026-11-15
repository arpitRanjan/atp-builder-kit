"""Run the acceptance cases and compare the pass rate with a ship bar you set.

The local app logic:   python scripts/acceptance.py --bar 0.8
A deployed app:        python scripts/acceptance.py --bar 0.8 --url https://your-app.onrender.com --out stage-05/acceptance-run.txt
The URL must take POST {"question": "..."} and reply with JSON {"text": "...", "cited": ["qn-01"]}.
app/api.py does this (see app/README.md). A URL with no path gets /ask added.
For a private Hugging Face Space, set ACCEPTANCE_TOKEN to an access token; it is sent as a Bearer header.
--out saves the same report, with the URL, date, model and ship bar at the top.
Exit code 0 when the pass rate meets the bar, 1 when it does not. Add KIT_OFFLINE=1 for the mock model.

Case fields (all optional except question; a case with no id is named case-01, case-02 ...):
  kind              normal, edge or failure (counted in the summary)
  cite_any          pass only if the reply cites at least one of these page ids
  never_cite        fail if the reply cites any of these page ids
  must_contain_any  pass only if the reply text has at least one of these words
  must_not_contain  fail if the reply text has any of these words
  expect_fallback   true: pass only if the app used a fallback. A fallback name: only that one.
"""
import argparse
import datetime as dt
import json
import os
import sys
from collections import Counter
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
CASES = ROOT / "evals" / "acceptance.jsonl"


def ask_local(question):
    from app.app import answer
    r = answer(question)
    return {"text": r["text"], "cited": r["cited"], "fallback": r.get("fallback"),
            "model": r["call"]["model"] if r.get("call") else None}


def ask_url(url, question):
    import requests
    if urlparse(url).path in ("", "/"):
        url = url.rstrip("/") + "/ask"
    headers = {}
    if os.environ.get("ACCEPTANCE_TOKEN"):
        headers["Authorization"] = f"Bearer {os.environ['ACCEPTANCE_TOKEN']}"
    resp = requests.post(url, json={"question": question}, headers=headers, timeout=120)  # free hosts wake slowly
    resp.raise_for_status()
    return resp.json()


def check(case, reply):
    """Reasons the case failed. An empty list means it passed."""
    reasons = []
    cited, text = set(reply.get("cited") or []), (reply.get("text") or "").lower()
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
    want = case.get("expect_fallback")
    got = reply.get("fallback")
    if want and not got:
        reasons.append("expected a fallback, got a normal answer")
    elif isinstance(want, str) and got != want:
        reasons.append(f"expected fallback '{want}', got '{got}'")
    return reasons


def run(cases, ask):
    rows = []
    for n, case in enumerate(cases, 1):
        try:
            reply = ask(case["question"])
            reasons = check(case, reply)
        except Exception as e:  # a crash or a bad reply counts as a failed case, not a crashed run
            reply, reasons = {}, [f"error: {type(e).__name__}: {e}"]
        rows.append({"id": case.get("id", f"case-{n:02d}"), "kind": case.get("kind", "normal"), "passed": not reasons,
                     "reasons": reasons, "model": reply.get("model")})
    return rows


def report(rows, bar, target, cases_path):
    passed = sum(r["passed"] for r in rows)
    rate = passed / len(rows)
    ok = rate >= bar
    models = sorted({r["model"] for r in rows if r["model"]}) or ["not reported"]
    kinds = Counter(r["kind"] for r in rows)
    kinds_passed = Counter(r["kind"] for r in rows if r["passed"])
    lines = [
        "Acceptance run",
        f"Target: {target}",
        f"Date (UTC): {dt.datetime.now(dt.timezone.utc).strftime('%Y-%m-%d %H:%M')}",
        f"Model: {', '.join(models)}",
        f"Cases: {cases_path} ({len(rows)} cases: " + ", ".join(f"{k} {v}" for k, v in sorted(kinds.items())) + ")",
        f"Ship bar: {bar:.0%}",
        "",
    ]
    lines += [f"{'pass' if r['passed'] else 'FAIL'} {r['id']} [{r['kind']}] {'; '.join(r['reasons'])}".rstrip() for r in rows]
    lines += ["", "By kind: " + ", ".join(f"{k} {kinds_passed[k]}/{v}" for k, v in sorted(kinds.items())),
              f"Pass rate {rate:.0%} ({passed}/{len(rows)}), ship bar {bar:.0%}: {'SHIP' if ok else 'DO NOT SHIP'}"]
    return "\n".join(lines), ok


def main(argv=None):
    parser = argparse.ArgumentParser(description="Acceptance cases against a ship bar.")
    parser.add_argument("--bar", type=float, required=True, help="ship bar as a pass rate from 0 to 1, like 0.8")
    parser.add_argument("--url", help="a deployed endpoint; leave out to test the local app logic")
    parser.add_argument("--cases", default=str(CASES))
    parser.add_argument("--out", help="also save the report to this file, like stage-05/acceptance-run.txt")
    args = parser.parse_args(argv)
    if not 0 <= args.bar <= 1:
        parser.error("--bar must be between 0 and 1")
    cases = [json.loads(line) for line in open(args.cases) if line.strip()]
    ask = (lambda q: ask_url(args.url, q)) if args.url else ask_local
    rows = run(cases, ask)
    target = args.url or "local app logic (app/app.py answer()), not a live URL"
    text, ok = report(rows, args.bar, target, args.cases)
    print(text)
    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(text + "\n")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
