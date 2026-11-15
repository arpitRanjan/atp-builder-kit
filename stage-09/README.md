# Stage 9: retrieval with permissions and cited answers

## Decisions

I chose **hybrid search (vector plus BM25, fused with RRF) at 120 word chunks, with no reranker**
(`retrieval_strategies.csv`):

| Setup (120 word chunks) | Recall@1 | Recall@3 | Recall@5 |
| --- | --- | --- | --- |
| vector | 0.74 | 0.92 | 0.94 |
| hybrid | 0.78 | 0.94 | 0.98 |
| hybrid + reranker | 0.70 | 0.94 | 0.98 |

Hybrid has the best recall at 1 and ties at 5. The reranker did not help here, and it adds a model to run.
The chunk size change to 40 words cut hybrid plus reranker recall at 5 to 0.88, so I kept 120.

The retrieval path beats the whole document baseline on the same 25 questions (`baseline_vs_retrieval.csv`):
accuracy 0.84 vs 0.80, at $0.000685 vs $0.004158 a question (about 6 times cheaper) and 516 vs 3,990 input tokens.

## What I measured

- Answers cite chunk ids, for example `[qn-02#0]` (`rag_answers.jsonl`).
- On 25 labeled questions (`evals/retrieval_questions.jsonl`), the chosen setup has recall@5 0.98 and citation
  faithfulness 0.88 (`retrieval_summary.json`, `retrieval_eval.csv`). The citation judge agreed with my labels
  on 21 of 25 planted cases (`citation_faithfulness.csv`).
- Two-user leak test (`leak_test.json`): ada (admin) gets an answer citing `qn-13#0`; pat (public) gets no
  admin chunk on any probe. The same test runs in CI (`.github/workflows/evals.yml`, `evals/retrieval_check.py`)
  and in `tests/test_permissions.py`.
- App: <link to your app change that calls `kit/rag.py` `answer_with_citations()` with the user's role>.

## Stale permission window

After qn-12 became admin only, a team user still saw it for **10 minutes** (minute 0 to 9) with the index alone:
the access lists sync every 15 minutes and results are cached for 5 (`stale_window.json`). With a live access
check before showing results, the window is 0 minutes. I decided to keep the live check.

## What is still weak

The live check covers results, not the cache of answers already shown. Recall is measured on 25 questions
written by me, from the same help pages.

## What I would do next

Re-index on every permission change (an event, not a 15 minute job), and add 20 questions from real traces.
