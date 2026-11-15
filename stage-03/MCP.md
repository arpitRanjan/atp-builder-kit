# MCP server setup

Output of `python mcp_server/describe.py`:

Server: `quillnote-docs` in `mcp_server/server.py`
Pinned in requirements.txt: `mcp==2.3.0` (installed: 2.3.0)
Documents folder (CORPUS_DIR): `corpus`

## Tool list

| Tool | Description | Inputs | Hints |
| --- | --- | --- | --- |
| `search_docs` | Find Quillnote help pages that answer a user's how-to question. Pass the question in plain words. Read-only: it never changes anything and makes no network calls. Returns up to top_k pages, best first, each with page id, title, visibility (public, team or admin) and a snippet. Do not show admin pages to end users. Cite the page id, like [qn-02], when you use a result. | query: string, top_k: integer | {"read_only_hint": true, "destructive_hint": false, "open_world_hint": false} |

## Rewritten tool description

Old: "Search the Quillnote help pages by keywords. Read-only: it never changes anything. Returns up to top_k
matching pages, best first, each with its page id, title, visibility (public, team or admin) and a short
snippet. Cite the page id when you use a result."

New: the description in the table above. It says when to use the tool, what to pass, that it makes no
network calls, and that admin pages must not reach end users.

## Scopes

| Tool | Reads | Writes | Network |
| --- | --- | --- | --- |
| `search_docs` | `CORPUS_DIR/*.md` only (the 15 Quillnote help pages) | nothing | none |

## MCP Inspector check

Checked on `<YYYY-MM-DD>` with `npx @modelcontextprotocol/inspector python mcp_server/server.py`:
`<what List Tools showed and one search you ran>`
