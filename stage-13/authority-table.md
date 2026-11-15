# Authority table

| Tool | Authority | Reversibility | Who approves | Worst likely mistake if it fires wrongly |
| --- | --- | --- | --- | --- |
| search_docs | reads help pages the user's role may see | nothing changes, fully reversible | nobody: always allowed | shows a page from another role if the role filter breaks |
| draft_issue | writes a draft to the local outbox | reversible: delete the draft, nothing is sent | a rule in code: the user's task asks for an issue and the address is on @quillnote.example; a person before any send | user data goes to an outside address because a page told the agent to |
| fetch_url | reads a URL | not reversible: anything in the URL has already left | the host allowlist inside the handler (help.quillnote.example only) | data leaks to an outside host through the query string |
