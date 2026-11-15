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

## Print its facts for stage-03/MCP.md

```
python mcp_server/describe.py
```

It asks the server for its tool list (the same call MCP Inspector makes) and prints the pinned `mcp`
version, each tool's description, inputs and hints. To rewrite the tool description, edit the
`description=` text in `server.py`, run `describe.py` again, and keep the old and new text in `MCP.md`.

## Test it with the MCP Inspector

The official Inspector needs Node.js:

```
npx @modelcontextprotocol/inspector python mcp_server/server.py
```

Open the link it prints, click **Connect**, then **Tools**, **List Tools**, pick `search_docs` and run it.
Write the date you did this in `stage-03/MCP.md`.

### In GitHub Codespaces

The Inspector runs inside the codespace, so your browser reaches it through a forwarded port.
The current Inspector (version 2) has one web port, 6274. It also prints a URL with a token. Use that token.

1. Start it so it accepts the forwarded address:

   ```
   ALLOWED_ORIGINS="https://${CODESPACE_NAME}-6274.${GITHUB_CODESPACES_PORT_FORWARDING_DOMAIN}" \
   MCP_INSPECTOR_ALLOWED_HOSTS=".${GITHUB_CODESPACES_PORT_FORWARDING_DOMAIN}" \
   MCP_AUTO_OPEN_ENABLED=false \
   npx @modelcontextprotocol/inspector python mcp_server/server.py
   ```

2. It prints a link like `http://localhost:6274/?MCP_INSPECTOR_API_TOKEN=...`. Copy the part from `?` on.
3. Open the **Ports** tab. Copy the forwarded address of port 6274. Open it in your browser with the
   copied `?MCP_INSPECTOR_API_TOKEN=...` part added to the end.
4. Connect, then use **Tools** as above.

An older Inspector (version 0.x) also runs a proxy on port 6277. With that one, open the forwarded 6274 page.
Under **Configuration**, set **Inspector Proxy Address** to the forwarded address of port 6277 (Ports tab).
Paste the session token it printed into **Proxy Session Token**. Then click **Connect**.
The codespace forwards both ports.

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
