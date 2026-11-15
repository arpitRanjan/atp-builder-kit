"""Stage 7 feedback: a thumbs down or an edited answer becomes one eval row (stage-07/feedback.jsonl).

Stage 8 turns these rows into golden set cases with to_golden_case(), so the feedback a person gives
in the app ends up as a test that runs on every pull request.
"""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

SIGNALS = ("thumbs_down", "thumbs_up", "edit")


def answer_id(prompt, answer):
    """A short stable id for one answer, so a feedback row points at exactly what was shown."""
    return "a-" + hashlib.md5(f"{prompt}\n{answer}".encode()).hexdigest()[:10]


def log_feedback(path, signal, prompt, answer, cited=None, edited_text=None, reason=None, session_id=None):
    """Append one eval row. signal is thumbs_down, thumbs_up or edit. Returns the row written."""
    if signal not in SIGNALS:
        raise ValueError(f"signal must be one of {SIGNALS}")
    if signal == "edit" and not edited_text:
        raise ValueError("an edit needs the edited text")
    row = {"timestamp": datetime.now(timezone.utc).isoformat(timespec="seconds"), "session_id": session_id,
           "signal": signal, "prompt": prompt, "answer_id": answer_id(prompt, answer), "answer": answer,
           "cited": list(cited or []), "edited_text": edited_text, "reason": reason}
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a") as f:
        f.write(json.dumps(row) + "\n")
    return row


def load_feedback(path):
    path = Path(path)
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()] if path.exists() else []


def to_golden_case(row, case_id, cite_any, split="dev"):
    """One golden.jsonl case from a feedback row. You still pick the page that should be cited."""
    case = {"question": row["prompt"], "cite_any": cite_any, "never_cite": "qn-13,qn-14,qn-15", "max_words": 120,
            "source": f"stage-07 feedback {row['answer_id']} ({row['signal']})", "split": split}
    if row.get("edited_text"):
        case["reference"] = row["edited_text"]
    return {"description": case_id, "vars": case}
