"""Hard and advisory gates for the golden set (evals/golden.jsonl).

Hard gates fail the run (and the pull request). Advisory gates are reported but never fail it.
Used by promptfoo (evals/promptfooconfig.yaml), by evals/run_evals.py and by the tests.
"""
import json
import re


def parse_output(output):
    # promptfoo hands over the provider output as text; run_evals.py passes the dict itself.
    return json.loads(output) if isinstance(output, str) else output


def as_list(value):
    # Page lists are comma separated text in golden.jsonl, because promptfoo turns a list var into many tests.
    if isinstance(value, str):
        return [v.strip() for v in value.split(",") if v.strip()]
    return list(value or [])


def hard_failures(case, result):
    """Reasons this answer must block a merge. An empty list means every hard gate passed."""
    fails = []
    text, cited = result.get("text", ""), set(result.get("cited", []))
    if not text.strip() or re.search(r"\bnot sure\b", text, re.I):
        fails.append("empty or unsure answer")
    if as_list(case.get("cite_any")) and not cited & set(as_list(case["cite_any"])):
        fails.append(f"cites none of {as_list(case['cite_any'])}")
    leaked = sorted(cited & set(as_list(case.get("never_cite"))))
    if leaked:
        fails.append(f"cites forbidden pages {leaked}")
    return fails


def advisory_warnings(case, result):
    """Things worth a look that should not block a merge."""
    warns = []
    n = len(result.get("text", "").split())
    if n > case.get("max_words", 120):
        warns.append(f"{n} words, over {case.get('max_words', 120)}")
    if len(result.get("cited", [])) > 2:
        warns.append("cites more than 2 pages")
    return warns


# promptfoo python assertions: get (output, context) and return a grading result.
def hard_gate(output, context):
    fails = hard_failures(context["vars"], parse_output(output))
    return {"pass": not fails, "score": 0.0 if fails else 1.0, "reason": "; ".join(fails) or "hard gates passed"}


def advisory_gate(output, context):
    warns = advisory_warnings(context["vars"], parse_output(output))
    return {"pass": True, "score": 0.0 if warns else 1.0, "reason": "advisory: " + ("; ".join(warns) or "ok")}
