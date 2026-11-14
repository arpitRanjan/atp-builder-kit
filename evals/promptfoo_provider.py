"""promptfoo provider: sends each golden question to the app's answer function (app/app.py)."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.app import answer  # noqa: E402


def call_api(prompt, options, context):
    r = answer(prompt)
    call = r["call"] or {}
    return {"output": json.dumps({"text": r["text"], "cited": r["cited"]}),
            "tokenUsage": {"prompt": call.get("input_tokens", 0), "completion": call.get("output_tokens", 0)}}
