"""A minimal Quillnote help assistant in Streamlit.

Run locally:  streamlit run app/app.py
Flow: question -> search_docs (same code as the MCP tool) -> call_llm with the snippets -> answer + cited page ids.
"""
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from kit.llm import call_llm  # noqa: E402
from mcp_server.server import search  # noqa: E402

# Config you can change.
MAX_CALLS_PER_SESSION = 10  # spend guard: stop after this many model calls per browser session
TOP_K = 3
SYSTEM = ("You are the Quillnote help assistant. Answer ONLY from the help pages given. "
          "Cite the page ids you used in square brackets, like [qn-01]. If the pages do not answer it, say so.")
KEY_NAMES = ["GEMINI_API_KEY", "FALLBACK_BASE_URL", "FALLBACK_API_KEY", "FALLBACK_MODEL", "KIT_PROVIDER"]


def build_prompt(question, hits):
    pages = "\n\n".join(f"[{h['id']}] {h['title']}\n{h['snippet']}" for h in hits)
    return f"Help pages:\n{pages}\n\nUser question: {question}"


def answer(question, folder=None):
    """Search, then ask the model. Returns the answer text, cited ids and the call record."""
    hits = search(question, TOP_K, folder)
    if not hits:
        return {"text": "No help page matches that question.", "cited": [], "hits": [], "call": None}
    call = call_llm(build_prompt(question, hits), system=SYSTEM, max_output_tokens=400)
    found = set(re.findall(r"qn-\d+", call["text"]))
    cited = [h["id"] for h in hits if h["id"] in found] or [h["id"] for h in hits]
    return {"text": call["text"], "cited": cited, "hits": hits, "call": call}


def guard_allows(calls_so_far, limit=MAX_CALLS_PER_SESSION):
    return calls_so_far < limit


def load_keys(secrets):
    # Streamlit Cloud keeps keys in st.secrets. Copy them to the environment for call_llm.
    for name in KEY_NAMES:
        try:
            if name in secrets and not os.environ.get(name):
                os.environ[name] = str(secrets[name])
        except Exception:
            pass  # no secrets file locally: fall back to env or .env


def main():
    import streamlit as st

    load_keys(st.secrets)
    st.title("Quillnote help assistant")
    st.caption("Answers come only from the Quillnote help pages. Demo app with synthetic data.")
    st.session_state.setdefault("calls", 0)
    question = st.text_input("Your question")
    if st.button("Ask") and question:
        if not guard_allows(st.session_state.calls):
            st.warning(f"Spend guard: this session used its {MAX_CALLS_PER_SESSION} calls. Reload later.")
            return
        st.session_state.calls += 1
        result = answer(question)
        st.write(result["text"])
        st.caption("Pages cited: " + (", ".join(result["cited"]) or "none"))
        st.caption(f"Calls this session: {st.session_state.calls} of {MAX_CALLS_PER_SESSION}")


if __name__ == "__main__":
    main()
