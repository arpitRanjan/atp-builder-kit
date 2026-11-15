"""Tool handlers for the app, with the Stage 13 host allowlist inside the handler.

fetch_url(url) reads one Quillnote help page by its URL. The check runs INSIDE the handler:
a URL whose host is not on ALLOWED_HOSTS never reaches the fetch, and the blocked call is
written as one JSON line to stage-13/blocked_calls.jsonl. This is an app level check, not
network sandboxing: code that skips this handler can still reach any host.

Use it in an agent loop like the one in notebooks/13_injection_and_redteam.ipynb:
    from app.tools import fetch_url
    TOOLS = {"search_docs": search_docs, "fetch_url": fetch_url}
To allow another host, add it to ALLOWED_HOSTS (exact names only, no wildcards).
"""
import sys
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
fetch_url = ALLOWLIST.guard(_fetch_help_page, tool="fetch_url")
fetch_url.__doc__ = ("Read a page from the Quillnote help site. Hosts not on ALLOWED_HOSTS are blocked "
                     "and logged to stage-13/blocked_calls.jsonl.")
