"""Stage 7: the help assistant with oversight. Approval screen, claim level citations, refusal state,
empty state and feedback logging, on top of the same answer() as app/app.py.

Run locally:   streamlit run stage-07/oversight_app.py
Deploy:        on Streamlit Community Cloud, pick this file as the app file (same secrets as app/app.py).
Logs:          stage-07/approvals.jsonl, stage-07/feedback.jsonl and stage-07/outbox.jsonl (set
               STAGE07_LOG_DIR to write them elsewhere). A deployed app cannot write into your repo,
               so use the download buttons in the sidebar and commit the files you download.
"""
import os
import sys
import time
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.app import answer, load_keys  # noqa: E402
from kit.approval import (SUGGESTED_PROMPTS, check_request, cite_claims, log_approval, propose_draft,  # noqa: E402
                          resolve_payload, seed_mistake, write_draft)
from kit.feedback import answer_id, log_feedback  # noqa: E402

LOG_DIR = Path(os.environ.get("STAGE07_LOG_DIR", Path(__file__).resolve().parent))
APPROVALS, FEEDBACK, OUTBOX = LOG_DIR / "approvals.jsonl", LOG_DIR / "feedback.jsonl", LOG_DIR / "outbox.jsonl"
FIELDS = ["title", "body", "related_pages", "visibility_of_pages", "destination", "requested_by", "run_id"]


def show_refusal(refusal):
    import streamlit as st
    st.error(f"**{refusal['limit']}**\n\nWhy: {refusal['reason']}\n\nWhat you can do: {refusal['next_step']}")


def cached_answer(question):
    """The answer shown for this question, made once. A rerun (a feedback click, a typed reason) reuses it,
    so there is no new model call and the feedback attaches to the answer the user saw."""
    import streamlit as st
    shown = st.session_state.get("shown")
    if not shown or shown["question"] != question:
        result = answer(question)
        shown = {"question": question, "result": result, "answer_id": answer_id(question, result["text"])}
        st.session_state.shown = shown
    return shown["result"], shown["answer_id"]


def show_answer(question, result, aid):
    import streamlit as st
    if result.get("fallback"):
        st.info(result["text"])
        return
    for n, c in enumerate(cite_claims(result["text"], result["hits"]), 1):
        cites = " ".join(f"`[{x['id']}] {x['title']}`" for x in c["citations"]) or ":orange[no source: check this]"
        st.markdown(f"**Claim {n}:** {c['claim']}  \nSource: {cites}")
    st.caption(f"Answer id: {aid}")
    with st.expander("Was this wrong? Tell us (writes an eval row)"):
        reason = st.text_input("What was wrong (optional)", key=f"reason-{aid}")
        edited = st.text_area("Or write the answer it should have given", key=f"edit-{aid}")
        down, save = st.columns(2)
        if down.button("Thumbs down", key=f"down-{aid}"):
            log_feedback(FEEDBACK, "thumbs_down", question, result["text"], result["cited"], reason=reason or None,
                         session_id=st.session_state.sid)
            st.success("Saved to feedback.jsonl")
        if save.button("Save my edit", key=f"save-{aid}", disabled=not edited):
            log_feedback(FEEDBACK, "edit", question, result["text"], result["cited"], edited_text=edited,
                         reason=reason or None, session_id=st.session_state.sid)
            st.success("Saved to feedback.jsonl")


def finish_decision(message):
    """After approve, edit or reject: clear the question box so the same request does not draft again."""
    import streamlit as st
    st.session_state.pending, st.session_state.editing, st.session_state.done = None, False, message
    st.session_state.question = ""
    st.session_state.pop("shown", None)
    st.rerun()


def approval_screen():
    """Approve, Edit or Reject the fully resolved draft_issue payload. Nothing is written before a decision."""
    import streamlit as st
    pending = st.session_state.pending
    payload = pending["payload"]
    st.subheader("Review this draft before it is saved")
    st.caption("Check every field. Approve saves it to the local outbox; nothing is sent anywhere.")
    st.table([{"field": f, "value": ", ".join(payload[f]) if isinstance(payload[f], list) else str(payload[f])}
              for f in FIELDS])
    if "admin" in payload["visibility_of_pages"]:
        st.warning("This draft links an admin only page. Check that it belongs here.")
    elapsed = lambda: round(time.time() - pending["shown_at"], 1)  # noqa: E731
    common = dict(session_id=st.session_state.sid, seeded_mistake=pending["seeded"])
    approve, edit, reject = st.columns(3)
    if approve.button("Approve", type="primary"):
        write_draft(OUTBOX, payload)
        log_approval(APPROVALS, payload["run_id"], "approve", payload, seconds_to_decide=elapsed(), **common)
        finish_decision("Approved and saved to the outbox.")
    if edit.button("Edit"):
        st.session_state.editing = True
    if reject.button("Reject"):
        log_approval(APPROVALS, payload["run_id"], "reject", payload, seconds_to_decide=elapsed(), **common)
        finish_decision("Rejected. Nothing was written.")
    if st.session_state.get("editing"):
        with st.form("edit-draft"):
            title = st.text_input("title", payload["title"])
            body = st.text_area("body", payload["body"])
            if st.form_submit_button("Save the edited draft"):
                edited = dict(payload, title=title, body=body)
                write_draft(OUTBOX, edited)
                log_approval(APPROVALS, payload["run_id"], "edit", payload, edited=edited,
                             seconds_to_decide=elapsed(), **common)
                finish_decision("Edited, approved and saved to the outbox.")


def main():
    import streamlit as st

    load_keys(st.secrets)
    st.title("Quillnote help assistant")
    st.caption("Answers come only from the Quillnote help pages. Demo app with synthetic data.")
    st.session_state.setdefault("sid", uuid.uuid4().hex[:8])
    st.session_state.setdefault("pending", None)
    st.session_state.setdefault("question", "")
    seed = st.sidebar.checkbox("Usability test: plant one mistake in the next draft")
    for path in (APPROVALS, FEEDBACK, OUTBOX):  # a deployed app cannot write to your repo: download, then commit
        if path.exists():
            st.sidebar.download_button(f"Download {path.name}", path.read_text(), file_name=path.name)
    if st.session_state.get("done"):
        st.success(st.session_state.pop("done"))
    if st.session_state.pending:
        approval_screen()
        return

    question = st.text_input("Your question, or ask me to draft an issue", key="question")
    if not question:  # the empty state
        st.markdown("**Not sure what to ask? Try one of these:**")
        for n, prompt in enumerate(SUGGESTED_PROMPTS):
            st.button(prompt, key=f"suggest-{n}", on_click=lambda p=prompt: st.session_state.update(question=p))
        return
    refusal = check_request(question)
    if refusal:
        show_refusal(refusal)
        return
    if "draft an issue" in question.lower() or "draft a bug" in question.lower():
        draft = propose_draft(question)
        if draft["args"] is None:
            st.info("I could not prepare a draft for that. Try: Draft an issue titled \"...\".")
            return
        payload = resolve_payload(draft)
        st.session_state.pending = {"payload": seed_mistake(payload) if seed else payload,
                                    "seeded": bool(seed), "shown_at": time.time()}
        st.rerun()
    show_answer(question, *cached_answer(question))


if __name__ == "__main__":
    main()
