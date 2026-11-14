# (d) the MCP search tool and (e) the app logic, on the fixture corpus.
import asyncio

from conftest import ROOT

FIXTURES = ROOT / "tests" / "fixtures" / "corpus"


def test_search_finds_pdf_page():
    from mcp_server.server import search
    hits = search("export a note as pdf", 3, FIXTURES)
    assert hits[0]["id"] == "qn-01" and hits[0]["snippet"]


def test_search_reads_visibility():
    from mcp_server.server import load_pages
    assert {p["visibility"] for p in load_pages(FIXTURES)} == {"public", "team", "admin"}


def test_tool_is_registered(monkeypatch):
    monkeypatch.setenv("CORPUS_DIR", str(FIXTURES))
    from mcp_server.server import mcp, search_docs
    assert search_docs("sync")[0]["id"] == "qn-02"
    names = [t.name for t in asyncio.run(mcp.list_tools())]
    assert names == ["search_docs"]


def test_app_logic_without_streamlit():
    from app.app import answer, build_prompt, guard_allows
    result = answer("How do I export a note as PDF?", folder=FIXTURES)
    assert "qn-01" in result["cited"] and result["call"]["provider"] == "mock"
    assert "[qn-01]" in build_prompt("q", result["hits"])
    assert guard_allows(0, 2) and not guard_allows(2, 2)
    assert answer("zzzz qqqq", folder=FIXTURES)["cited"] == []
