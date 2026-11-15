"""Print the MCP server's facts for stage-03/MCP.md: pinned version, tool list, descriptions and scopes.

Run:  python mcp_server/describe.py > stage-03/mcp_tools.md
It asks the real server for its tool list (the same call MCP Inspector makes), so the output matches what clients see.
"""
import asyncio
import json
import os
import sys
from importlib.metadata import version
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from mcp_server.server import corpus_dir, mcp  # noqa: E402


def describe():
    tools = asyncio.run(mcp.list_tools())
    pinned = next((line.strip() for line in open(ROOT / "requirements.txt") if line.startswith("mcp==")), "not pinned")
    lines = [f"Server: `{mcp.name}` in `mcp_server/server.py`",
             f"Pinned in requirements.txt: `{pinned}` (installed: {version('mcp')})",
             f"Documents folder (CORPUS_DIR): `{os.path.relpath(corpus_dir(), ROOT)}`", "",
             "| Tool | Description | Inputs | Hints |", "| --- | --- | --- | --- |"]
    for t in tools:
        inputs = ", ".join(f"{k}: {v.get('type', '?')}" for k, v in t.input_schema.get("properties", {}).items())
        hints = json.dumps(t.annotations.model_dump(exclude_none=True)) if t.annotations else "none"
        lines.append(f"| `{t.name}` | {t.description} | {inputs} | {hints} |")
    return "\n".join(lines)


if __name__ == "__main__":
    print(describe())
