"""The graders for the golden set (evals/golden.jsonl): two code graders, one model judge, one advisory check.

- citation grader (code, hard): the answer is not empty or unsure, cites one of cite_any, never cites never_cite.
- content grader (code, hard): the answer never says a must_not_contain phrase and, when must_contain_any
  is set, says one of those phrases. Regression cases (split "regression") use it, like the sycophancy flip.
- model judge: the judge from notebooks/08_judge_calibration.ipynb grades the answer against the case's
  reference. It is advisory until you trust it: set JUDGE_HARD=1 once its true positive and true negative
  rates from that notebook are good enough, and then a judge FAIL fails the run.
- advisory (code): length and number of cited pages. Reported, never fails the run.

Hard failures fail the run (and the pull request). Used by promptfoo (evals/promptfooconfig.yaml),
by evals/run_evals.py and by the tests.
"""
import json
import os
import re
import sys
from pathlib import Path


def parse_output(output):
    # promptfoo hands over the provider output as text; run_evals.py passes the dict itself.
    return json.loads(output) if isinstance(output, str) else output


def as_list(value):
    # Page lists are comma separated text in golden.jsonl, because promptfoo turns a list var into many tests.
    if isinstance(value, str):
        return [v.strip() for v in value.split(",") if v.strip()]
    return list(value or [])


def citation_failures(case, result):
    """Code grader 1: the answer exists, cites one of the right pages and no forbidden page."""
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


def content_failures(case, result):
    """Code grader 2: phrases the answer must never say, and phrases it must say (any one of them)."""
    fails, text = [], result.get("text", "").lower()
    for phrase in as_list(case.get("must_not_contain")):
        if phrase.lower() in text:
            fails.append(f"says '{phrase}'")
    need = as_list(case.get("must_contain_any"))
    if need and not any(p.lower() in text for p in need):
        fails.append(f"says none of {need}")
    return fails


def hard_failures(case, result):
    """Reasons this answer must block a merge. An empty list means both code graders passed."""
    return citation_failures(case, result) + content_failures(case, result)


def advisory_warnings(case, result):
    """Things worth a look that should not block a merge."""
    warns = []
    n = len(result.get("text", "").split())
    if n > case.get("max_words", 120):
        warns.append(f"{n} words, over {case.get('max_words', 120)}")
    if len(result.get("cited", [])) > 2:
        warns.append("cites more than 2 pages")
    return warns


# The same judge prompt that notebooks/08_judge_calibration.ipynb measures. Change both together.
JUDGE_SYSTEM = ("You grade answers from a help assistant. PASS only if the answer is correct and fully "
                "supported by the reference. Any wrong detail, invented feature or refusal is a FAIL. "
                "Reply with PASS or FAIL, a colon, then one short reason.")


def judge_is_hard():
    return os.environ.get("JUDGE_HARD") == "1"


def judge_verdict(case, result):
    """The model judge. Returns ("pass" | "fail" | "unparsed", reason), or (None, ...) with no reference."""
    if not case.get("reference"):
        return None, "no reference in this case"
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # promptfoo loads this file on its own
    from kit.llm import call_llm
    r = call_llm(f"Question: {case['question']}\nReference: {case['reference']}\nAnswer: {result.get('text', '')}\n"
                 "Reply with PASS or FAIL.", system=JUDGE_SYSTEM, max_output_tokens=800)
    verdict = re.match(r"\s*(PASS|FAIL)", r["text"].upper())
    return (verdict.group(1).lower() if verdict else "unparsed"), r["text"].strip()[:200]


# promptfoo python assertions: get (output, context) and return a grading result.
def hard_gate(output, context):
    fails = hard_failures(context["vars"], parse_output(output))
    return {"pass": not fails, "score": 0.0 if fails else 1.0, "reason": "; ".join(fails) or "hard gates passed"}


def citation_gate(output, context):
    fails = citation_failures(context["vars"], parse_output(output))
    return {"pass": not fails, "score": 0.0 if fails else 1.0, "reason": "; ".join(fails) or "citations ok"}


def content_gate(output, context):
    fails = content_failures(context["vars"], parse_output(output))
    return {"pass": not fails, "score": 0.0 if fails else 1.0, "reason": "; ".join(fails) or "content ok"}


def judge_gate(output, context):
    verdict, reason = judge_verdict(context["vars"], parse_output(output))
    ok = verdict in (None, "pass")
    return {"pass": ok or not judge_is_hard(), "score": 1.0 if ok else 0.0,
            "reason": f"judge {verdict or 'skipped'}: {reason}" + ("" if judge_is_hard() else " (advisory)")}


def advisory_gate(output, context):
    warns = advisory_warnings(context["vars"], parse_output(output))
    return {"pass": True, "score": 0.0 if warns else 1.0, "reason": "advisory: " + ("; ".join(warns) or "ok")}
