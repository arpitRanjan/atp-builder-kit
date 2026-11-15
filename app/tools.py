"""Tool handlers for the app, with the Stage 13 defenses inside the handlers.

fetch_url(url) reads one Quillnote help page by its URL. The check runs INSIDE the handler:
a URL whose host is not on ALLOWED_HOSTS never reaches the fetch, and the blocked call is
written as one JSON line to stage-13/blocked_calls.jsonl. This is an app level check, not
network sandboxing: code that skips this handler can still reach any host.
To allow another host, add it to ALLOWED_HOSTS (exact names only, no wildcards).

draft_issue(title, body, approved=False, to=...) is the state-changing tool. It refuses unless
approved is True AND the address is on TEAM_DOMAIN. Pass approved=True only after a person said yes
(the Approve button in stage-07/oversight_app.py). Approved drafts go to stage-13/outbox.jsonl,
refused ones to stage-13/held_drafts.jsonl. Nothing is ever sent anywhere.

notebooks/13_injection_and_redteam.ipynb builds its defended tools from this file
(make_fetch_url and approval_gate), so a fix here shows in stage-13/redteam-outcomes.csv on rerun.
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
TEAM_DOMAIN = "@quillnote.example"  # drafts may only be addressed to the team
BLOCKED_LOG = ROOT / "stage-13" / "blocked_calls.jsonl"
OUTBOX = ROOT / "stage-13" / "outbox.jsonl"  # drafts that were approved and written. Nothing is sent anywhere
HELD_LOG = ROOT / "stage-13" / "held_drafts.jsonl"  # drafts the gate refused, for review
CORPUS = ROOT / "corpus"
DENIED = "DENIED: a human did not approve this draft. Nothing was written."


def _append(path, rec):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a") as f:
        f.write(json.dumps(rec) + "\n")


# ---------- fetch_url, with the host allowlist ----------
def make_fetch_url(corpus=None, log_path=BLOCKED_LOG, on_fetch=None):
    """A fetch_url handler wrapped by HostAllowlist(...).guard(...). It never touches the network:
    the page id at the end of the URL is read from the local help pages (corpus may be a folder, or a
    function that returns one). on_fetch(url) is called for every URL that passed the allowlist.
    The handler's allowlist is handler.allowlist (its .blocked list holds the blocked calls)."""
    allowlist = HostAllowlist(ALLOWED_HOSTS, log_path=log_path)

    def fetch_help_page(url):
        if on_fetch:
            on_fetch(url)
        folder = corpus() if callable(corpus) else corpus
        page_id = url.split("?", 1)[0].rstrip("/").rsplit("/", 1)[-1]
        path = Path(folder or CORPUS) / f"{page_id}.md"
        if not path.name.startswith("qn-") or not path.exists():
            return {"url": url, "text": "not found"}
        return {"url": url, "text": path.read_text()[:600]}

    guarded = allowlist.guard(fetch_help_page, tool="fetch_url")
    guarded.allowlist = allowlist
    guarded.__doc__ = ("Read a page from the Quillnote help site. Hosts not on ALLOWED_HOSTS are blocked "
                       "and logged.")
    return guarded


fetch_url = make_fetch_url()
ALLOWLIST = fetch_url.allowlist


# ---------- draft_issue, with an approval gate ----------
def draft_issue(title, body, approved=False, to="docs" + TEAM_DOMAIN, outbox=None, held_log=None, extra=None):
    """Save a draft bug report, only when a person approved it and it goes to the team. The gate is here,
    in code: the model cannot talk its way past it. A refused draft is logged and nothing is written."""
    rec = {"time": datetime.now(timezone.utc).isoformat(timespec="seconds"), "tool": "draft_issue",
           "to": to, "title": title, "body": body, **(extra or {})}
    why = None
    if approved is not True:
        why = "not approved by a person"
    elif not str(to).endswith(TEAM_DOMAIN):
        why = f"the address is not on {TEAM_DOMAIN}"
    if why:
        _append(held_log or HELD_LOG, dict(rec, reason=why))
        return {"saved": False, "denied": True, "reason": f"{DENIED} ({why})"}
    _append(outbox or OUTBOX, dict(rec, approved=True))
    return {"saved": True, "denied": False, "to": to}


def task_asks_for_issue(task):
    """The approval rule the red team notebook uses as its stand-in for a person: the user's own
    task asked for an issue. In the live app a person clicks Approve instead."""
    return any(w in task.lower() for w in ("issue", "bug report"))


def approval_gate(task, approve=task_asks_for_issue, outbox=None, held_log=None, extra=None, on_held=None):
    """A draft_issue handler for one task: approved only when approve(task) says yes.
    extra() may return fields to add to each record (the notebook adds its run name).
    on_held(record) is called for every refused draft."""
    def gated(title, body, to="docs" + TEAM_DOMAIN):
        fields = extra() if callable(extra) else (extra or {})
        out = draft_issue(title, body, approved=bool(approve(task)), to=to, outbox=outbox, held_log=held_log,
                          extra=fields)
        if out["denied"] and on_held:
            on_held({**fields, "to": to, "title": title})
        return out
    return gated
