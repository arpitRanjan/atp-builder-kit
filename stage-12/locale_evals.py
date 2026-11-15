"""Stage 12: the Spanish variant of the help answer, and its eval run for CI.

The variant: translate the question into English for search only, then answer in the user's language.
The golden set is stage-12/golden-set.jsonl (made by notebooks/12_locale_eval.ipynb from evals/golden_es.jsonl).
The same hard gates as Stage 8 (evals/gates.py) score every case.

Run:   python stage-12/locale_evals.py            (add KIT_OFFLINE=1 to use the mock model)
       python stage-12/locale_evals.py --bar 0.8 --out stage-12/results/ci-results.json
Exit code 1 when the hard gate pass rate is under the bar, so CI can block the pull request.
"""
import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "evals"))

from gates import hard_failures  # noqa: E402

GOLDEN = HERE / "golden-set.jsonl"
STARTER = ROOT / "evals" / "golden_es.jsonl"
TRANSLATE = "Translate this help question into English. Reply with the English question only."


def starter_cases(path=STARTER, corpus_questions=None):
    """The kit's Spanish cases, in the stage-12 golden set shape: input, expected, source."""
    corpus_questions = corpus_questions or ROOT / "corpus" / "questions.jsonl"
    english = {q["qid"]: q["question"] for q in map(json.loads, open(corpus_questions))}
    rows = []
    for c in map(json.loads, open(path)):
        v = c["vars"]
        rows.append({"id": c["description"], "kind": c["kind"], "degradation": c.get("degradation", "none"),
                     "input": v["question"], "expected": v["cite_any"],
                     "source": f"kit practice data: corpus/questions.jsonl {c['source_qid']} "
                               f"(\"{english[c['source_qid']]}\"), translated by hand",
                     "never_cite": v.get("never_cite", ""), "max_words": v.get("max_words", 120)})
    return rows


def load_cases(path=GOLDEN):
    path = Path(path)
    if not path.exists():
        return starter_cases()
    return [json.loads(line) for line in open(path) if line.strip()]


def gate_vars(case):
    return {"question": case["input"], "cite_any": case["expected"], "never_cite": case.get("never_cite", ""),
            "max_words": case.get("max_words", 120)}


def localized_ask(question, folder=None):
    """The variant feature: English search, answer in the user's language."""
    from app.app import SYSTEM, TOP_K, build_prompt
    from kit.llm import call_llm
    from mcp_server.server import search

    english = call_llm(f"Question: {question}", system=TRANSLATE, max_output_tokens=1000)["text"].strip()
    hits = search(english, TOP_K, folder)
    if not hits:
        return {"text": "No help page matches that question.", "cited": [], "search_query": english}
    r = call_llm(build_prompt(question, hits), system=SYSTEM + " Reply in the language of the user question.",
                 max_output_tokens=400)
    found = set(re.findall(r"qn-\d+", r["text"]))
    cited = [h["id"] for h in hits if h["id"] in found] or [h["id"] for h in hits]
    return {"text": r["text"], "cited": cited, "search_query": english}


def score(cases, ask, setup):
    rows = []
    for c in cases:
        out = ask(c["input"])
        fails = hard_failures(gate_vars(c), out)
        rows.append({"setup": setup, "id": c["id"], "kind": c["kind"], "degradation": c.get("degradation", "none"),
                     "input": c["input"], "expected": c["expected"], "output": out["text"], "cited": out["cited"],
                     "passed": not fails, "why": "; ".join(fails)})
    return rows


def main(argv=None):
    parser = argparse.ArgumentParser(description="Run the Stage 12 Spanish golden set through the variant.")
    parser.add_argument("--golden", default=str(GOLDEN))
    parser.add_argument("--bar", type=float, default=0.8, help="lowest hard gate pass rate that passes CI")
    parser.add_argument("--out", default=str(HERE / "results" / "ci-results.json"))
    args = parser.parse_args(argv)
    from kit.llm import default_model, pick_provider

    cases = load_cases(args.golden)
    rows = score(cases, localized_ask, "variant")
    for r in rows:
        print(f"{'pass' if r['passed'] else 'FAIL'}  {r['id']}  {r['kind']}/{r['degradation']}  {r['why']}")
    rate = sum(r["passed"] for r in rows) / len(rows)
    provider = pick_provider()
    result = {"time": datetime.now(timezone.utc).isoformat(timespec="seconds"), "provider": provider,
              "model": default_model(provider), "cases": len(rows), "passed": sum(r["passed"] for r in rows),
              "pass_rate": round(rate, 3), "bar": args.bar, "gate": "pass" if rate >= args.bar else "fail",
              "rows": rows}
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=1, ensure_ascii=False) + "\n")
    print(f"\nSpanish hard gates: {result['passed']}/{len(rows)} passed ({rate:.0%}), bar {args.bar:.0%}. "
          f"Results in {out.relative_to(ROOT) if out.is_relative_to(ROOT) else Path(out.parent.parent.name, out.parent.name, out.name)}")
    return 0 if rate >= args.bar else 1


if __name__ == "__main__":
    sys.exit(main())
