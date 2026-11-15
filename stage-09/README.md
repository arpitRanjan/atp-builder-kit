# Stage 9: a retrieval layer with permissions and cited answers

Submit: the GitHub link to your repo's `stage-09/` folder.

## Checklist: files in stage-09/

| File | What it must show | Made by |
| --- | --- | --- |
| `09_rag_pipeline.ipynb` | Parse, chunk, embed, a local index, retrieve, and answers that cite chunk ids like `[qn-02#0]` | your run of `notebooks/09_rag_pipeline.ipynb` |
| `rag_answers.jsonl` | The saved run: every answer with the chunk ids it retrieved and cited | `09_rag_pipeline`, step 6 |
| `baseline_vs_retrieval.csv` | The whole document baseline (every page in the prompt) vs the retrieval path, on the same questions: accuracy, tokens, cost, latency | `09_rag_pipeline`, step 10 |
| `09_retrieval_eval.ipynb` | Recall at k and citation faithfulness | your run of `notebooks/09_retrieval_eval.ipynb` |
| `retrieval_strategies.csv` | vector, hybrid and hybrid with a reranker at one chunk size (120 words), then one chunk size change (40 words). bm25 is a reference row | `09_retrieval_eval`, step 5 |
| `citation_faithfulness.csv` | Cited chunk per answer, labeled faithful or not, and the judge's verdict | `09_retrieval_eval`, step 7 |
| `retrieval_eval.csv`, `retrieval_summary.json`, `leak_test.json` | Recall at k and citation faithfulness on the 20+ labeled questions, and the two-user leak test, from the same script CI runs | `09_retrieval_eval`, step 8 (`python evals/retrieval_check.py --out stage-09`) |
| `09_permissions.ipynb` | Access lists on chunks, the query-time filter, the two-user leak test | your run of `notebooks/09_permissions.ipynb` |
| `stale_window.json` | The stale permission window after a permission change, in minutes, from a real run | `09_permissions`, step 5 |
| `README.md` | The sections below | you |

## In the eval suite and CI (outside stage-09/)

- `evals/retrieval_questions.jsonl`: the labeled questions (25 in the kit; keep 20 or more, add your own).
  Each has `page_ids` (the right pages) and `role` (who may read them). The three 09 notebooks and CI both
  read this file, so a question you add here shows in both.
- `evals/retrieval_check.py`: recall at k, citation faithfulness and the two-user leak test. It exits 1 below
  `--min-recall` or `--min-faithful`, or on any leak. `.github/workflows/evals.yml.example` runs it on every pull request.
  That CI step answers with the offline mock (`KIT_OFFLINE: "1"`), so free tier rate limits cannot fail it.
  Recall and the leak test need no model. Set it to `"0"` to grade citations with your real model.
- `tests/test_permissions.py`: the same leak test in pytest.
- The app: answer through `kit/rag.py` `answer_with_citations(question, search, role)` with the user's role.
  Link your app change from the README.

There is no index file to commit: the notebooks rebuild the index in seconds.

## README.md sections (use these headings)

- `## Decisions` (the setup you chose and why, in numbers from `retrieval_strategies.csv`)
- `## What I measured` (recall at k, citation faithfulness, the baseline comparison, the leak test)
- `## Stale permission window` (the number, and what you decided)
- `## What is still weak`
- `## What I would do next`
