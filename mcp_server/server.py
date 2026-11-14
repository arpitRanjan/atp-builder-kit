"""An MCP server with ONE read-only tool: search_docs. It searches the markdown help pages in corpus/.

Run:   python mcp_server/server.py          (talks MCP over stdio)
Pages folder: CORPUS_DIR env var, default corpus/ next to this folder.
Built with the official MCP Python SDK. In mcp 2.x the class FastMCP is called MCPServer.
"""
import os
import re
from pathlib import Path

from mcp.server.mcpserver import MCPServer
from mcp.types import ToolAnnotations

ROOT = Path(__file__).resolve().parent.parent


def corpus_dir():
    return Path(os.environ.get("CORPUS_DIR", ROOT / "corpus"))


def load_pages(folder=None):
    """Read every .md page (except README.md) into a dict: id, title, visibility, body."""
    pages = []
    for path in sorted(Path(folder or corpus_dir()).glob("*.md")):
        if path.name.lower() == "readme.md":
            continue
        text = path.read_text()
        meta, body = {}, text
        if text.startswith("---"):
            _, head, body = text.split("---", 2)
            for line in head.strip().splitlines():
                key, _, value = line.partition(":")
                meta[key.strip()] = value.strip()
        pages.append({"id": meta.get("id", path.stem), "title": meta.get("title", path.stem),
                      "visibility": meta.get("visibility", "public"), "body": body.strip()})
    return pages


def words(text):
    return set(re.findall(r"[a-z0-9]+", text.lower())) - {"the", "a", "an", "to", "i", "how", "do", "my", "is", "of"}


def search(query, top_k=3, folder=None):
    """Keyword search: score = number of query words found in the page title and body."""
    q = words(query)
    scored = []
    for page in load_pages(folder):
        score = len(q & words(page["title"])) * 2 + len(q & words(page["body"]))
        if score > 0:
            scored.append((score, page))
    scored.sort(key=lambda pair: -pair[0])
    return [{"id": p["id"], "title": p["title"], "visibility": p["visibility"], "score": s,
             "snippet": p["body"][:240]} for s, p in scored[:top_k]]


mcp = MCPServer("quillnote-docs")


@mcp.tool(
    description=(
        "Search the Quillnote help pages by keywords. Read-only: it never changes anything. "
        "Returns up to top_k matching pages, best first, each with its page id, title, visibility "
        "(public, team or admin) and a short snippet. Cite the page id when you use a result."
    ),
    annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False, openWorldHint=False),
)
def search_docs(query: str, top_k: int = 3) -> list[dict]:
    """query: the user's question or keywords. top_k: how many pages to return (1 to 10)."""
    return search(query, max(1, min(int(top_k), 10)))


if __name__ == "__main__":
    mcp.run()
