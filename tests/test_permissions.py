# The two-user leak test: a public user must never retrieve admin (or team) pages.
import copy
import json

import pytest

from conftest import ROOT

from kit.rag import ACCESS, BM25Index, HashEmbedder, VectorIndex, chunk_pages, parse_corpus

PAGES = parse_corpus(ROOT / "corpus")
CHUNKS = chunk_pages(PAGES, 120, 30)
VISIBILITY = {p["id"]: p["visibility"] for p in PAGES}
PROBES = [json.loads(line)["question"] for line in open(ROOT / "corpus" / "questions.jsonl")]
PROBES += ["refund a double charge", "read the audit log", "delete a user's data", "admin console billing payments"]


@pytest.fixture(scope="module", params=["vector", "bm25"])
def index(request):
    return VectorIndex(CHUNKS, HashEmbedder()) if request.param == "vector" else BM25Index(CHUNKS)


def seen(index, role, k=5):
    return {VISIBILITY[c["page_id"]] for q in PROBES for c, _ in index.search(q, k=k, role=role)}


def test_every_chunk_has_its_page_access_list():
    assert all(c["access"] == ACCESS[VISIBILITY[c["page_id"]]] for c in CHUNKS)


def test_public_user_never_gets_admin_or_team_pages(index):
    assert seen(index, "public") == {"public"}


def test_team_user_never_gets_admin_pages(index):
    assert "admin" not in seen(index, "team")


def test_admin_user_can_read_admin_pages(index):
    assert "admin" in seen(index, "admin")


def test_without_the_filter_it_would_leak(index):
    # Proves the test can fail: with no role filter, admin pages come back.
    assert "admin" in seen(index, None)


def test_stale_copy_leaks_until_reindex():
    changed = "qn-12"  # team page made admin only
    query = "How do shared templates work for a team workspace?"
    stale = VectorIndex(CHUNKS, HashEmbedder())
    assert any(c["page_id"] == changed for c, _ in stale.search(query, k=3, role="team"))
    fresh_chunks = copy.deepcopy(CHUNKS)
    for c in fresh_chunks:
        if c["page_id"] == changed:
            c["access"] = ACCESS["admin"]
    fresh = VectorIndex(fresh_chunks, HashEmbedder())
    assert not any(c["page_id"] == changed for c, _ in fresh.search(query, k=3, role="team"))
