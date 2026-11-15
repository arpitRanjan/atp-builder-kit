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
HIDE_VISIBILITY = ["admin"]  # Stage 3 fix: users never see admin only pages (backlog rank 9)
PROMPT_FILE = ROOT / "prompts" / "help_v2.md"  # the versioned system prompt in use
SYSTEM = PROMPT_FILE.read_text().strip()
KEY_NAMES = ["GEMINI_API_KEY", "FALLBACK_BASE_URL", "FALLBACK_API_KEY", "FALLBACK_MODEL", "KIT_PROVIDER"]

# Fallbacks: what the user sees when a named failure happens, instead of an error or a made up answer.
FALLBACKS = {
    "no_page": "No help page matches that question. Try other words, or contact Quillnote support.",
    "model_error": "The assistant cannot answer right now. Please try again in a minute, or contact Quillnote support.",
    # Stage 5 PRD failure mode "billing question": hand off to a person, never give refund steps.
    "billing_handoff": ("Billing questions go to a person. Contact Quillnote support with your invoice number "
                        "and they will check the charge. The assistant cannot issue refunds."),
}
BILLING_WORDS = {"refund", "refunded", "charged", "charge", "billed", "invoice", "payment", "payments"}


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
    if BILLING_WORDS & set(re.findall(r"[a-z]+", question.lower())):
        return fallback("billing_handoff")
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


# ---------- Ready, not on by default: answer through kit/rag.py (Chapter 9 retrieval with role filters) ----------
# To switch: in main() (and app/api.py) call answer_rag(question, role) instead of answer(question).
# It needs numpy and rank_bm25 (both in app/requirements.txt). Without sentence-transformers, kit/rag.py
# falls back to the small hash embedder and prints a note, so it works on Streamlit Cloud with no torch.
RAG_STRATEGY = "hybrid"  # vector, hybrid or hybrid_rerank (see kit/rag.py)
_RAG = {}


def _rag_search(folder=None):
    from kit.rag import chunk_pages, make_search, parse_corpus
    key = (str(folder), RAG_STRATEGY)
    if key not in _RAG:
        pages = parse_corpus(folder)
        _RAG[key] = (make_search(chunk_pages(pages), RAG_STRATEGY), {p["id"]: p for p in pages})
    return _RAG[key]


def answer_rag(question, role="public", folder=None, model=None, provider=None):
    """Like answer(), with kit.rag search for this role. Returns the same keys: text, cited (page ids),
    hits (id, title, visibility, snippet), call and fallback."""
    from kit.rag import answer_with_citations
    search, pages = _rag_search(folder)
    found = [(c, s) for c, s in search(question, TOP_K * 3, role)
             if pages[c["page_id"]]["visibility"] not in HIDE_VISIBILITY][:TOP_K]
    hits = []
    for c, _ in found:
        if c["page_id"] not in {h["id"] for h in hits}:
            page = pages[c["page_id"]]
            hits.append({"id": page["id"], "title": page["title"], "visibility": page["visibility"],
                         "snippet": c["text"]})
    if not hits:
        return fallback("no_page")
    llm_args = {k: v for k, v in {"model": model, "provider": provider}.items() if v}
    try:
        r = answer_with_citations(question, lambda q, k=TOP_K, role=None: found, role, TOP_K, **llm_args)
    except LLMError:
        return fallback("model_error", hits)
    cited = [h["id"] for h in hits if h["id"] in r["cited_pages"]] or [h["id"] for h in hits]
    return {"text": r["text"], "cited": cited, "hits": hits, "call": r["call"], "fallback": None}


# Example: wrap the answer with the Stage 13 guardrails (kit/guardrails.py). Not on by default.
#
# from kit.guardrails import RateLimiter, SpendCap, guarded_answer, input_rules, model_input_check
# LIMITER, CAP = RateLimiter(5, 60), SpendCap(5.0)  # 5 questions per user a minute, $5 a day
#
# def check(q):
#     ok, reason = input_rules(q)
#     return (ok, reason, None) if not ok else model_input_check(q)
#
# def guarded(question, role="public", user_id="demo-user"):
#     hits = search(question, TOP_K * 3)  # no model call: the page visibilities the output check needs
#     generate = lambda q: answer(q)  # noqa: E731  or answer_rag(q, role); runs alongside the input check
#     return guarded_answer(question, user_id, generate, check, role=role,
#                           visibility={h["id"]: h["visibility"] for h in hits}, limiter=LIMITER, cap=CAP)


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
