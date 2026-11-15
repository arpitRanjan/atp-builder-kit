"""Stage 11: the answer function for the Northwind deployment.

notebooks/11_customer_deployment.ipynb imports this file. It does not keep its own copy.
So a change you make here changes what the notebook measures:
  answer()              the "before": retrieve for the role, answer from those sources only
  answer_with_support() the "after": the one change Step 7 ships (always give a way out)
Edit SYSTEM, SUPPORT_LINE or answer_with_support() for your own change, rerun the notebook,
and commit this file. Its commit hash goes in your stage-11 README.
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from kit.llm import call_llm  # noqa: E402

SYSTEM = ("Answer using only the numbered sources. Cite the source ids you used in square brackets, like [nw-02#0]. "
          "If the sources do not answer the question, say so and tell the user to contact support.")
SUPPORT = re.compile(r"contact support", re.I)
SUPPORT_LINE = "If this does not answer your question, contact support at support@northwind.example."


def answer(question, role, index, qid="adhoc", audit=None, k=3):
    """Retrieve with this role's filter, answer from those chunks only. Returns (text, cited pages, retrieved pages).

    index is a kit.rag VectorIndex. audit(action, role, qid, retrieved, cited, call) is called once, if given.
    """
    hits = index.search(question, k=k, role=role)  # the role filter from Chapter 9, with their roles
    sources = "\n".join(f"[{c['id']}] {c['text']}" for c, _ in hits)
    r = call_llm(f"Sources:\n{sources}\n\nQuestion: {question}", system=SYSTEM, max_output_tokens=1000)
    cited = {c.split("#")[0] for c in re.findall(r"nw-\d+(?:#\d+)?", r["text"])}
    retrieved = [c["page_id"] for c, _ in hits]
    if audit:
        audit("answer", role, qid, retrieved, cited, r)
    return r["text"], cited, retrieved


def answer_with_support(question, role, index, qid="adhoc", audit=None):
    """The shipped change: when no page answered it, the answer always ends with a pointer to support."""
    text, cited, retrieved = answer(question, role, index, qid, audit)
    if not cited and not SUPPORT.search(text):
        text = f"{text} {SUPPORT_LINE}"
    return text, cited, retrieved
