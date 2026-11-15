"""A minimal Quillnote help assistant in Streamlit.

Run locally:  streamlit run app/app.py
Flow: question -> search_docs (same code as the MCP tool) -> call_llm with the snippets -> answer + cited page ids.
The same answer() function also backs the HTTP endpoint in app/api.py (POST /ask).
"""
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from kit.llm import LLMError, call_llm  # noqa: E402
from mcp_server.server import search  # noqa: E402

# Config you can change.
MAX_CALLS_PER_SESSION = 10  # spend guard: stop after this many model calls per browser session
TOP_K = 3
HIDE_VISIBILITY = []  # page visibilities the app never reads, for example ["admin"]
PROMPT_FILE = ROOT / "prompts" / "help_v1.md"  # the versioned system prompt in use
SYSTEM = PROMPT_FILE.read_text().strip()
KEY_NAMES = ["GEMINI_API_KEY", "FALLBACK_BASE_URL", "FALLBACK_API_KEY", "FALLBACK_MODEL", "KIT_PROVIDER"]

# Fallbacks: what the user sees when a named failure happens, instead of an error or a made up answer.
FALLBACKS = {
    "no_page": "No help page matches that question. Try other words, or contact Quillnote support.",
    "model_error": "The assistant cannot answer right now. Please try again in a minute, or contact Quillnote support.",
}


def build_prompt(question, hits):
    pages = "\n\n".join(f"[{h['id']}] {h['title']}\n{h['snippet']}" for h in hits)
    return f"Help pages:\n{pages}\n\nUser question: {question}"


def fallback(reason, hits=None):
    """The fallback reply for one named failure. 'fallback' says which one fired."""
    return {"text": FALLBACKS[reason], "cited": [], "hits": hits or [], "call": None, "fallback": reason}


def answer(question, folder=None, model=None, provider=None):
    """Search, then ask the model. Returns the answer text, cited ids, the call record and the fallback used.

    model and provider are optional: leave them out to use the kit's default (see kit/llm.py).
    """
    hits = [h for h in search(question, TOP_K * 3, folder) if h["visibility"] not in HIDE_VISIBILITY][:TOP_K]
    if not hits:
        return fallback("no_page")
    try:
        call = call_llm(build_prompt(question, hits), system=SYSTEM, max_output_tokens=400, model=model, provider=provider)
    except LLMError:
        return fallback("model_error", hits)
    found = set(re.findall(r"qn-\d+", call["text"]))
    cited = [h["id"] for h in hits if h["id"] in found] or [h["id"] for h in hits]
    return {"text": call["text"], "cited": cited, "hits": hits, "call": call, "fallback": None}


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
        if result["fallback"]:
            st.info(result["text"])
            st.caption(f"Fallback used: {result['fallback']}")
        else:
            st.write(result["text"])
            st.caption("Pages cited: " + (", ".join(result["cited"]) or "none"))
        st.caption(f"Calls this session: {st.session_state.calls} of {MAX_CALLS_PER_SESSION}")


if __name__ == "__main__":
    main()
