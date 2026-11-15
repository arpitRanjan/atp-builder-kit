"""Retrieval parts shared by the 09 notebooks and the tests: parse, chunk, embed, index, search, rerank.

notebooks/09_rag_pipeline.ipynb builds the same steps one by one; this file packages them.
Under KIT_OFFLINE=1 (or KIT_EMBEDDER=hash) the embedder and reranker are deterministic
stand-ins, so nothing is downloaded. Otherwise they are small local models from Hugging Face.
"""
import hashlib
import os
import re
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
EMBED_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
RERANK_MODEL = "cross-encoder/ms-marco-MiniLM-L-6-v2"
# Who may read a page with each visibility.
ACCESS = {"public": ["public", "team", "admin"], "team": ["team", "admin"], "admin": ["admin"]}
STOP = {"the", "a", "an", "to", "i", "how", "do", "my", "is", "of", "and", "or", "in", "on", "for", "it",
        "can", "what", "me", "you", "your", "be", "with", "this", "that", "are", "if", "at", "as", "by"}


def tokens(text):
    return [w for w in re.findall(r"[a-z0-9]+", text.lower()) if w not in STOP]


def parse_corpus(folder=None):
    """Read every page in corpus/ (not README.md): id, title, visibility from the front matter, and body."""
    pages = []
    for path in sorted(Path(folder or ROOT / "corpus").glob("*.md")):
        if path.name.lower() == "readme.md":
            continue
        _, head, body = path.read_text().split("---", 2)
        meta = dict(line.split(":", 1) for line in head.strip().splitlines())
        meta = {k.strip(): v.strip() for k, v in meta.items()}
        pages.append({"id": meta["id"], "title": meta["title"], "visibility": meta["visibility"],
                      "body": body.strip()})
    return pages


def chunk_pages(pages, size=120, overlap=30, access=None):
    """Split each page into chunks of `size` words that share `overlap` words with the previous chunk.

    access maps a page visibility to the roles that may read it (default ACCESS). Another customer
    with other roles passes its own map, like data/customer_northwind does.
    """
    access = access or ACCESS
    chunks = []
    step = max(1, size - overlap)
    for page in pages:
        ws = page["body"].split()
        for n, start in enumerate(range(0, max(len(ws) - overlap, 1), step)):
            text = " ".join(ws[start:start + size])
            chunks.append({"id": f"{page['id']}#{n}", "page_id": page["id"], "title": page["title"],
                           "text": text, "access": access[page["visibility"]]})
    return chunks


class HashEmbedder:
    """Deterministic stand-in for a sentence embedding model: hashed words and word pairs."""

    name = "hash-384"

    def __init__(self, dim=384):
        self.dim = dim

    def encode(self, texts):
        out = np.zeros((len(texts), self.dim), dtype=np.float32)
        for row, text in enumerate(texts):
            ws = [w[:-1] if len(w) > 3 and w.endswith("s") else w for w in tokens(text)]
            for feat in ws + [a + "_" + b for a, b in zip(ws, ws[1:])]:
                h = int(hashlib.md5(feat.encode()).hexdigest(), 16)
                out[row, h % self.dim] += 1.0 if (h >> 20) % 2 else -1.0
        return out / np.maximum(np.linalg.norm(out, axis=1, keepdims=True), 1e-9)


class LocalEmbedder:
    """all-MiniLM-L6-v2 through sentence-transformers. Downloads about 90 MB the first time."""

    name = "all-MiniLM-L6-v2"

    def __init__(self):
        from sentence_transformers import SentenceTransformer
        self.model = SentenceTransformer(EMBED_MODEL, device="cpu")

    def encode(self, texts):
        return np.asarray(self.model.encode(list(texts), normalize_embeddings=True), dtype=np.float32)


def use_stand_ins():
    return os.environ.get("KIT_OFFLINE") == "1" or os.environ.get("KIT_EMBEDDER") == "hash"


def get_embedder():
    return HashEmbedder() if use_stand_ins() else LocalEmbedder()


class VectorIndex:
    """A numpy matrix of chunk vectors. Search is one matrix product; no database."""

    def __init__(self, chunks, embedder):
        self.chunks, self.embedder = list(chunks), embedder
        self.vectors = embedder.encode([c["text"] for c in self.chunks])

    def search(self, query, k=5, role=None):
        scores = self.vectors @ self.embedder.encode([query])[0]
        order = np.argsort(-scores)
        hits = [(self.chunks[i], float(scores[i])) for i in order if allowed(self.chunks[i], role)]
        return hits[:k]


def allowed(chunk, role):
    # role None means no filter (an internal tool). A real app always passes the user's role.
    return role is None or role in chunk["access"]


class BM25Index:
    """Keyword search with BM25 (rank_bm25)."""

    def __init__(self, chunks):
        from rank_bm25 import BM25Okapi
        self.chunks = list(chunks)
        self.bm25 = BM25Okapi([tokens(c["text"]) for c in self.chunks])

    def search(self, query, k=5, role=None):
        scores = self.bm25.get_scores(tokens(query))
        order = np.argsort(-scores)
        hits = [(self.chunks[i], float(scores[i])) for i in order if allowed(self.chunks[i], role)]
        return hits[:k]


def rrf(rankings, k=5, c=60):
    """Reciprocal rank fusion: each list gives 1 / (c + rank). Returns the top k chunks."""
    score, by_id = {}, {}
    for hits in rankings:
        for rank, (chunk, _) in enumerate(hits, start=1):
            score[chunk["id"]] = score.get(chunk["id"], 0.0) + 1.0 / (c + rank)
            by_id[chunk["id"]] = chunk
    best = sorted(score, key=lambda i: -score[i])[:k]
    return [(by_id[i], score[i]) for i in best]


class OverlapReranker:
    """Deterministic stand-in for a cross-encoder: query words and word pairs found in the chunk."""

    name = "overlap-stand-in"

    def score(self, query, texts):
        q = tokens(query)
        pairs = set(zip(q, q[1:]))
        out = []
        for t in texts:
            tw = tokens(t)
            out.append(len(set(q) & set(tw)) + 2 * len(pairs & set(zip(tw, tw[1:]))) - len(tw) / 1000)
        return out


class CrossEncoderReranker:
    """cross-encoder/ms-marco-MiniLM-L-6-v2 through sentence-transformers. About 90 MB the first time."""

    name = "ms-marco-MiniLM-L-6-v2"

    def __init__(self):
        from sentence_transformers import CrossEncoder
        self.model = CrossEncoder(RERANK_MODEL, device="cpu")

    def score(self, query, texts):
        return [float(s) for s in self.model.predict([(query, t) for t in texts])]


def get_reranker():
    return OverlapReranker() if use_stand_ins() else CrossEncoderReranker()


def rerank(reranker, query, hits, k=5):
    scores = reranker.score(query, [c["text"] for c, _ in hits])
    order = sorted(range(len(hits)), key=lambda i: -scores[i])
    return [(hits[i][0], scores[i]) for i in order[:k]]


# ---------- the retrieval answer path (Stage 9): one search function, answers that cite chunk ids ----------
ANSWER_SYSTEM = ("Answer using only the numbered sources. Cite the source ids you used in square brackets, "
                 "like [qn-02#0]. If the sources do not answer the question, say so.")
STRATEGIES = ("vector", "hybrid", "hybrid_rerank")


def make_search(chunks, strategy="hybrid_rerank", embedder=None, reranker=None):
    """Returns search(query, k, role) for one strategy. Every strategy filters by role at query time."""
    vector = VectorIndex(chunks, embedder or get_embedder())
    if strategy == "vector":
        return vector.search
    keyword = BM25Index(chunks)

    def hybrid(query, k=5, role=None):
        return rrf([vector.search(query, 20, role), keyword.search(query, 20, role)], k)
    if strategy == "hybrid":
        return hybrid
    ranker = reranker or get_reranker()
    return lambda query, k=5, role=None: rerank(ranker, query, hybrid(query, 20, role), k)


def answer_with_citations(question, search, role=None, k=3, **llm_args):
    """Retrieve for this user's role, answer from those chunks only, and keep the chunk ids it cites."""
    from kit.llm import call_llm
    hits = search(question, k, role)
    sources = "\n".join(f"[{c['id']}] {c['text']}" for c, _ in hits)
    r = call_llm(f"Sources:\n{sources}\n\nQuestion: {question}", system=ANSWER_SYSTEM, max_output_tokens=1000,
                 **llm_args)
    ids = {c["id"] for c, _ in hits}
    cited = [i for i in dict.fromkeys(re.findall(r"qn-\d+#\d+", r["text"])) if i in ids]
    return {"question": question, "role": role, "text": r["text"], "retrieved": [c["id"] for c, _ in hits],
            "cited_chunks": cited, "cited_pages": sorted({i.split("#")[0] for i in cited}), "call": r}
