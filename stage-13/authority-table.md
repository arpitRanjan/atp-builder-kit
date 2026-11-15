# Authority table

One row per tool the assistant can call. The handlers are in `app/tools.py` and `mcp_server/server.py`.
Change the rows to match your tools. Notebook 13 Step 11 keeps this file if it exists.

| Tool | Authority | Reversibility | Who approves | Worst likely mistake if it fires wrongly |
| --- | --- | --- | --- | --- |
| search_docs | reads help pages the user's role may see | nothing changes, fully reversible | nobody: always allowed | shows a page from another role if the role filter breaks |
| fetch_url | reads a URL | not reversible: anything in the URL has already left | the host allowlist inside the handler (`app/tools.py`, help.quillnote.example only) | data leaks to an outside host through the query string |
| draft_issue | writes a draft to the local outbox (`stage-13/outbox.jsonl`) | reversible: delete the draft, nothing is sent | a person: the handler refuses unless `approved=True` (`app/tools.py`) | user data goes into a draft because a page told the agent to |
