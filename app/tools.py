"""Tool handlers for the app, with the Stage 13 host allowlist inside the handler.

fetch_url(url) reads one Quillnote help page by its URL. The check runs INSIDE the handler:
a URL whose host is not on ALLOWED_HOSTS never reaches the fetch, and the blocked call is
written as one JSON line to stage-13/blocked_calls.jsonl. This is an app level check, not
network sandboxing: code that skips this handler can still reach any host.

Use it in an agent loop like the one in notebooks/13_injection_and_redteam.ipynb:
    from app.tools import fetch_url
    TOOLS = {"search_docs": search_docs, "fetch_url": fetch_url}
To allow another host, add it to ALLOWED_HOSTS (exact names only, no wildcards).

draft_issue(title, body, approved=False) is the state-changing tool. It refuses unless approved is True,
so pass approved=True only after a person clicked Approve (as in stage-07/oversight_app.py).
Approved drafts go to stage-13/outbox.jsonl; refused ones to stage-13/held_drafts.jsonl.
The authority table for these tools is stage-13/authority-table.md.
"""
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from kit.guardrails import HostAllowlist  # noqa: E402

ALLOWED_HOSTS = {"help.quillnote.example"}
BLOCKED_LOG = ROOT / "stage-13" / "blocked_calls.jsonl"
CORPUS = ROOT / "corpus"


def _fetch_help_page(url, corpus=None):
    """The raw handler. It never touches the network: the page id at the end of the URL is read
    from the local help pages, for example https://help.quillnote.example/qn-02."""
    page_id = url.split("?", 1)[0].rstrip("/").rsplit("/", 1)[-1]
    path = Path(corpus or CORPUS) / f"{page_id}.md"
    if not path.name.startswith("qn-") or not path.exists():
        return {"url": url, "text": "not found"}
    return {"url": url, "text": path.read_text()[:600]}


ALLOWLIST = HostAllowlist(ALLOWED_HOSTS, log_path=BLOCKED_LOG)
OUTBOX = ROOT / "stage-13" / "outbox.jsonl"  # drafts that were approved and written. Nothing is sent anywhere
HELD_LOG = ROOT / "stage-13" / "held_drafts.jsonl"  # drafts the gate refused, for review


def _append(path, rec):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a") as f:
        f.write(json.dumps(rec) + "\n")


def draft_issue(title, body, approved=False, outbox=None, held_log=None):
    """Save a draft bug report, but only when a person approved it. The gate is here, in code: the model
    cannot talk its way past it. A refused draft is logged to held_drafts.jsonl and nothing is written."""
    rec = {"time": datetime.now(timezone.utc).isoformat(timespec="seconds"), "tool": "draft_issue",
           "title": title, "body": body}
    if approved is not True:
        _append(held_log or HELD_LOG, dict(rec, reason="not approved by a person"))
        return {"saved": False, "denied": True,
                "reason": "DENIED: a human did not approve this draft. Nothing was written."}
    _append(outbox or OUTBOX, dict(rec, approved=True))
    return {"saved": True, "denied": False}
fetch_url = ALLOWLIST.guard(_fetch_help_page, tool="fetch_url")
fetch_url.__doc__ = ("Read a page from the Quillnote help site. Hosts not on ALLOWED_HOSTS are blocked "
                     "and logged to stage-13/blocked_calls.jsonl.")
