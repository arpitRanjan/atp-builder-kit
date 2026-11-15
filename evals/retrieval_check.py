"""The Stage 9 retrieval eval and two-user leak test, in one command for CI.

Run:      python evals/retrieval_check.py            (add KIT_OFFLINE=1 for the mock model and stand-ins)
Options:  --strategy vector|hybrid|hybrid_rerank   (default hybrid_rerank)  --size 120 --overlap 30
          --k 5  --min-recall 0.8  --min-faithful 0.7  --out stage-09   (write the result files there)
Labeled questions: evals/retrieval_questions.jsonl (qid, question, page_ids, role: who may read the pages).
Exit code 1 when recall at k or citation faithfulness is under its bar, or when the leak test leaks.
"""
import argparse
import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from kit.rag import STRATEGIES, answer_with_citations, chunk_pages, make_search, parse_corpus  # noqa: E402

QUESTIONS = ROOT / "evals" / "retrieval_questions.jsonl"
# The two users of the leak test: one may read admin pages, one may not.
USERS = {"ada (admin)": "admin", "pat (public)": "public"}
LEAK_PROBES = ["How do I request a refund for being charged twice?", "refund a double charge", "read the audit log",
               "delete a user's data", "admin console billing payments"]


def recall_at_k(retrieved_pages, page_ids, k):
    return len(set(retrieved_pages[:k]) & set(page_ids)) / len(page_ids)


def evaluate(search, questions, k=5):
    """One row per labeled question: recall at 1, 3 and k, and whether the cited chunks are faithful."""
    rows = []
    for q in questions:
        pages = [c["page_id"] for c, _ in search(q["question"], k, q.get("role"))]
        a = answer_with_citations(q["question"], search, q.get("role"))
        faithful = bool(a["cited_pages"]) and set(a["cited_pages"]) <= set(q["page_ids"])
        rows.append({"qid": q["qid"], "role": q.get("role"), "question": q["question"],
                     "labeled_pages": ",".join(q["page_ids"]), "recall@1": recall_at_k(pages, q["page_ids"], 1),
                     "recall@3": recall_at_k(pages, q["page_ids"], 3), f"recall@{k}": recall_at_k(pages, q["page_ids"], k),
                     "cited_chunks": ",".join(a["cited_chunks"]), "citation_faithful": faithful,
                     "answer": a["text"][:200]})
    return rows


def leak_test(search, blocked_pages, k=5):
    """The admin user gets an answer with citations; the public user never sees a blocked chunk."""
    out = {}
    for user, role in USERS.items():
        seen = [c["id"] for q in LEAK_PROBES for c, _ in search(q, k, role) if c["page_id"] in blocked_pages]
        a = answer_with_citations(LEAK_PROBES[0], search, role)
        out[user] = {"role": role, "admin_chunks_retrieved": sorted(set(seen)), "answer": a["text"][:200],
                     "cited_chunks": a["cited_chunks"]}
    admin, public = out["ada (admin)"], out["pat (public)"]
    out["passed"] = bool(admin["cited_chunks"]) and not public["admin_chunks_retrieved"] \
        and not set(public["cited_chunks"]) & {c for c in admin["cited_chunks"]}
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--strategy", choices=STRATEGIES, default="hybrid_rerank")
    ap.add_argument("--size", type=int, default=120)
    ap.add_argument("--overlap", type=int, default=30)
    ap.add_argument("--k", type=int, default=5)
    ap.add_argument("--min-recall", type=float, default=0.8)
    ap.add_argument("--min-faithful", type=float, default=0.7)
    ap.add_argument("--questions", default=str(QUESTIONS))
    ap.add_argument("--out", help="folder for retrieval_eval.csv, retrieval_summary.json and leak_test.json")
    args = ap.parse_args(argv)

    pages = parse_corpus()
    search = make_search(chunk_pages(pages, args.size, args.overlap), args.strategy)
    questions = [json.loads(line) for line in open(args.questions) if line.strip()]
    rows = evaluate(search, questions, args.k)
    recall = sum(r[f"recall@{args.k}"] for r in rows) / len(rows)
    faithful = sum(r["citation_faithful"] for r in rows) / len(rows)
    leak = leak_test(search, {p["id"] for p in pages if p["visibility"] == "admin"}, args.k)
    summary = {"strategy": args.strategy, "chunk_size": args.size, "overlap": args.overlap, "questions": len(rows),
               f"recall@{args.k}": round(recall, 3), "citation_faithfulness": round(faithful, 3),
               "min_recall": args.min_recall, "min_faithful": args.min_faithful, "leak_test_passed": leak["passed"]}
    summary["passed"] = recall >= args.min_recall and faithful >= args.min_faithful and leak["passed"]

    print(f"{len(rows)} labeled questions | {args.strategy}, {args.size} word chunks")
    print(f"Recall@{args.k}: {recall:.2f} (bar {args.min_recall}) | citation faithfulness: {faithful:.2f} "
          f"(bar {args.min_faithful})")
    for user in USERS:
        u = leak[user]
        print(f"Leak test, {user}: cited {u['cited_chunks'] or 'nothing'}, admin only chunks retrieved: "
              f"{u['admin_chunks_retrieved'] or 'none'}")
    print("Leak test:", "passed" if leak["passed"] else "FAILED", "| overall:", "passed" if summary["passed"] else "FAILED")
    if args.out:
        out = Path(args.out)
        out.mkdir(parents=True, exist_ok=True)
        with open(out / "retrieval_eval.csv", "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0]))
            w.writeheader()
            w.writerows(rows)
        (out / "retrieval_summary.json").write_text(json.dumps(summary, indent=1) + "\n")
        (out / "leak_test.json").write_text(json.dumps(leak, indent=1) + "\n")
    return 0 if summary["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
