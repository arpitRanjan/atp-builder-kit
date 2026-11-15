"""Stage 7 oversight helpers: the draft approval payload and log, claim level citations, the refusal
state and the empty state. stage-07/oversight_app.py builds its screens from these; the tests use them too.

The draft action is the Stage 6 one: draft_issue saves a bug report to a LOCAL outbox file and sends
nothing anywhere. Here the model proposes the draft, and nothing is written until a person approves it.
"""
import json
import re
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from kit.llm import call_llm  # noqa: E402
from mcp_server.server import load_pages, search  # noqa: E402

# The empty state: shown before the first question. Keep at least 3.
SUGGESTED_PROMPTS = [
    "How do I export a note as PDF?",
    "I deleted a note by accident. Can I get it back?",
    'PDF export cuts off wide tables. Draft an issue titled "PDF export cuts off tables".',
]

# The refusal state: what the assistant will not do, why, and what the user can do instead.
REFUSALS = [
    {"kind": "admin_only", "pattern": r"\b(refund|audit log|admin console|delete (a|another|this|the) user|"
                                      r"delete .*user'?s data|change (the )?billing)\b",
     "limit": "I cannot do admin actions or show admin only steps.",
     "reason": "Refunds, user deletion, billing changes and the audit log are for workspace admins only.",
     "next_step": "Ask your workspace admin, or ask me how to find who your admin is."},
    {"kind": "other_users_data",
     "pattern": r"\b(all users|every user|everyone['’]s|other users'?|(someone|somebody|anyone|anybody) else['’]s|"
                r"another (person|user|member|customer|teammate|colleague)['’]s|other (people|person)['’]s|"
                r"(my )?(coworker|co-worker|colleague|teammate)['’]s (notes?|notebooks?|account|data))\b",
     "limit": "I cannot look up other people's notes or account details.",
     "reason": "Each person can only see their own notes and the notebooks shared with them.",
     "next_step": "Ask the owner to share the notebook with you, or ask me how sharing works."},
    {"kind": "prompt_leak", "pattern": r"\b(system prompt|your instructions|hidden rules)\b",
     "limit": "I cannot share my setup instructions.",
     "reason": "They are part of how the product works, not help content.",
     "next_step": "Ask me a question about using Quillnote, for example how to export a note."},
    {"kind": "out_of_scope", "pattern": r"\b(medical|diagnos|legal advice|lawyer|invest|stock|tax return)\w*",
     "limit": "I only answer questions about using Quillnote.",
     "reason": "My answers come from the Quillnote help pages, which do not cover this.",
     "next_step": "Try one of the suggested questions, or search the help pages by keyword."},
]


def check_request(text):
    """Returns the structured refusal for an unsupported or unsafe request, or None when it is fine."""
    for rule in REFUSALS:
        if re.search(rule["pattern"], text, re.I):
            return {k: rule[k] for k in ("kind", "limit", "reason", "next_step")}
    return None


# ---------- claim level citations ----------
def _words(text):
    return {w for w in re.findall(r"[a-z0-9]+", text.lower()) if len(w) > 3}


def cite_claims(text, hits):
    """Split an answer into claims (sentences) and attach the page each claim rests on.

    A page id the model wrote in the sentence wins ("model"). Otherwise the hit sharing the most
    words with the sentence is used ("matched"), and a claim that shares under 2 words with every
    hit gets no source ("none"), so the UI can flag it instead of hiding it.
    """
    by_id = {h["id"]: h for h in hits}
    claims = []
    for sentence in re.split(r"(?<=[a-z)\]*][.!?])\s+", text.strip()):  # "1." in a list is not a claim end
        if not sentence:
            continue
        ids = [i for i in re.findall(r"qn-\d+", sentence) if i in by_id]
        how = "model"
        if not ids and hits:
            best = max(hits, key=lambda h: len(_words(sentence) & _words(h["title"] + " " + h["snippet"])))
            if len(_words(sentence) & _words(best["title"] + " " + best["snippet"])) >= 2:
                ids, how = [best["id"]], "matched"
        if not ids:
            how = "none"
        claim = re.sub(r"\s*\[qn-\d+(?:#\d+)?\]", "", sentence).strip()
        claims.append({"claim": claim, "how": how,
                       "citations": [{"id": i, "title": by_id[i]["title"]} for i in dict.fromkeys(ids)]})
    return claims


# ---------- the draft and its approval ----------
DRAFT_SYSTEM = """You are an agent for the Quillnote help desk.
TOOL PROTOCOL: reply with exactly one JSON object and nothing else.
To call a tool: {"tool": "<name>", "args": {<arguments>}}
To finish:      {"final": "<answer for the user, citing page ids like [qn-02]>"}
Tools:
- search_docs(query: str, top_k: int = 3): search the Quillnote help pages. Read-only.
- draft_issue(title: str, body: str): save a draft bug report to the local outbox. Use it only when the task asks for an issue.
Every reply is JSON, your final answer too. Never reply with plain text.
Call one tool per reply. Finish as soon as you can answer."""


def propose_draft(request, folder=None, max_steps=4):
    """Run the Stage 6 loop until the model asks for draft_issue, and return that call WITHOUT running it.

    Returns {"run_id", "args", "hits", "steps"}; args is None when the model never asked for a draft.
    """
    steps, hits = [], []
    for _ in range(max_steps):
        lines = [f"Task: {request}", "", "Steps so far:"]
        for n, s in enumerate(steps, 1):
            lines += [f"CALL {n}: {json.dumps(s['call'])}", f"RESULT {n}: {s['result']}"]
        if not steps:
            lines.append("(none yet)")
        reply = call_llm("\n".join(lines + ["", "Reply with your next JSON object."]), system=DRAFT_SYSTEM,
                         max_output_tokens=1000)["text"]
        try:
            action = json.loads(reply[reply.find("{"): reply.rfind("}") + 1])
        except ValueError:
            break
        if action.get("tool") == "search_docs":
            found = search(action.get("args", {}).get("query", request), 3, folder)
            hits += [h for h in found if h["id"] not in {x["id"] for x in hits}]
            steps.append({"call": action, "result": json.dumps(found)})
        elif action.get("tool") == "draft_issue":
            return {"run_id": uuid.uuid4().hex[:8], "args": action.get("args", {}), "hits": hits, "steps": steps}
        else:
            break
    return {"run_id": uuid.uuid4().hex[:8], "args": None, "hits": hits, "steps": steps}


def resolve_payload(draft, folder=None, requested_by="this session"):
    """The FULLY resolved payload a person reviews: every field the action will write, nothing hidden."""
    args, titles = draft["args"] or {}, {p["id"]: p for p in load_pages(folder)}
    body = str(args.get("body", ""))
    related = [i for i in dict.fromkeys(re.findall(r"qn-\d+", body)) if i in titles]
    return {"action": "draft_issue", "destination": "local outbox file (outbox.jsonl). Nothing is sent.",
            "run_id": draft["run_id"], "title": str(args.get("title", "")), "body": body,
            "related_pages": [f"{i} {titles[i]['title']}" for i in related],
            "visibility_of_pages": sorted({titles[i]["visibility"] for i in related}),
            "requested_by": requested_by}


def seed_mistake(payload, folder=None):
    """For the usability test: swap the first related page for an unrelated one, the mistake to catch."""
    pages = {p["id"]: p["title"] for p in load_pages(folder) if p["visibility"] == "public"}
    used = {r.split()[0] for r in payload["related_pages"]}
    wrong = [i for i in sorted(pages) if i not in used][-1]  # the last public page: unrelated to most drafts
    out = dict(payload, related_pages=[f"{wrong} {pages[wrong]}"] + payload["related_pages"][1:])
    out["body"] = re.sub(r"qn-\d+", wrong, payload["body"], count=1) if re.search(r"qn-\d+", payload["body"]) \
        else payload["body"] + f" Related pages: {wrong}."
    return out


def diff(before, after):
    """Field by field changes: {field: [old, new]} for every field that differs."""
    return {k: [before.get(k), after.get(k)] for k in sorted(set(before) | set(after)) if before.get(k) != after.get(k)}


def log_approval(path, run_id, outcome, payload, edited=None, session_id=None, seconds_to_decide=None,
                 seeded_mistake=False):
    """Append one approval event (approve, edit or reject). Returns the row written."""
    if outcome not in ("approve", "edit", "reject"):
        raise ValueError("outcome must be approve, edit or reject")
    row = {"timestamp": datetime.now(timezone.utc).isoformat(timespec="seconds"), "session_id": session_id,
           "run_id": run_id, "outcome": outcome, "payload": edited or payload,
           "payload_diff": diff(payload, edited) if edited else {}, "seconds_to_decide": seconds_to_decide,
           "seeded_mistake": seeded_mistake}
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a") as f:
        f.write(json.dumps(row) + "\n")
    return row


def write_draft(outbox, payload):
    """The state change itself, called only after approve or edit. Local file only."""
    outbox = Path(outbox)
    outbox.parent.mkdir(parents=True, exist_ok=True)
    with open(outbox, "a") as f:
        f.write(json.dumps({"run_id": payload["run_id"], "title": payload["title"], "body": payload["body"]}) + "\n")
