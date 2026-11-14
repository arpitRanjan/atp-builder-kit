# mcp_server

An MCP server with ONE read-only tool:

- `search_docs(query: str, top_k: int = 3)`: keyword search over the help pages in `corpus/*.md`.
  Returns page ids, titles, visibility and snippets.

Built with the official MCP Python SDK (`mcp` package). In `mcp` 2.x the class that older guides call
`FastMCP` is named `MCPServer`; it is the same idea.

## Run it

First make the corpus (`python corpus/make_corpus.py`), or point it at the test pages:

```
export CORPUS_DIR=tests/fixtures/corpus   # optional, default is corpus/
python mcp_server/server.py
```

It talks MCP over stdio, so it waits silently for a client. Stop it with Ctrl+C.

## Test it with the MCP Inspector

The official Inspector needs Node.js:

```
npx @modelcontextprotocol/inspector python mcp_server/server.py
```

Open the link it prints, click **Connect**, then **Tools**, **List Tools**, pick `search_docs` and run it.

## Optional: use it from Claude Desktop

Add this to Claude Desktop's `claude_desktop_config.json` (use full paths):

```json
{
  "mcpServers": {
    "quillnote-docs": {
      "command": "/full/path/to/atp-builder-kit/.venv/bin/python",
      "args": ["/full/path/to/atp-builder-kit/mcp_server/server.py"],
      "env": { "CORPUS_DIR": "/full/path/to/atp-builder-kit/corpus" }
    }
  }
}
```

## Supply-chain habit

- **Pin versions.** `requirements.txt` pins `mcp` and everything else. Do the same for any server you install.
- **List tools and scopes.** Before you connect any MCP server, list its tools and what each can reach.
  This one: 1 tool, `search_docs`, read-only, reads files in `CORPUS_DIR` only, no network, no writes.
