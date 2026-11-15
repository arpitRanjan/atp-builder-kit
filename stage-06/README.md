# Stage 6: an agent loop for one feature

Submit: the GitHub link to your repo's `stage-06/` folder.

Build the agent version of ONE feature from your Stage 5 PRD on your own loop. The kit example feature:
answer a Quillnote help question with cited pages, and draft a bug report when the user asks for one.
Change the tasks, tools and checks in `notebooks/06_harness.ipynb` to fit your feature.

## Checklist: files in stage-06/

| File | What it must show | Made by |
| --- | --- | --- |
| `06_harness.ipynb` | Your loop with 2 or 3 tools: `search_docs` (your Stage 3 MCP search tool, from `mcp_server/server.py`) and `draft_issue` (a mock state-changing tool that writes only to a local file). All five controls in code: `STEP_BUDGET`, `SPEND_BUDGET_USD`, `MAX_RETRIES` (capped retry), the approval check (`APPROVED`), and `validate_final` with `MAX_VALIDATION_RETRIES = 1` | your run of `notebooks/06_harness.ipynb`, saved here |
| `traces/run.jsonl` | One JSON line per step: `run_id`, `step`, `action`, and the `stop`, `retry`, `validation`, `approval` and `error` flags | `06_harness`, step 6 |
| `pass_rates.csv` | 10 tasks, 7 rows: all on, all off, and one row each with only the step budget, spend budget, capped retry, approval check or validation turned off | `06_harness`, step 7 |
| `runs.csv` | One row per run (70 runs), with its stop reason and cost | `06_harness`, step 6 |
| `outbox.jsonl` | What the mock tool wrote. Nothing was sent anywhere | `06_harness` |
| `failed_run.md` | One failed run, step by step from the trace, with the failing layer named. Fill in the "Why" part yourself | `06_harness`, step 9 |
| `06_context_ablation.ipynb` | Block ablation, compaction and memory, on the same feature and help pages | your run of `notebooks/06_context_ablation.ipynb` |
| `context_ablation.csv` | The context ablation table | `06_context_ablation`, step 5 |
| `compaction_check.csv` | The compaction check: which constraints survive a summary, before and after pinning | `06_context_ablation`, steps 7 and 8 |
| `README.md` | The five sections below | you |

`06_agent_loop` and `06_structured_output` are practice notebooks. They are not required for this stage.

## README.md sections (use these headings)

- `## Why this feature needs an agent` (and not a fixed workflow)
- `## Controls I chose and why`
- `## What I measured` (the pass-rate table and what the numbers say)
- `## What failed` (link `failed_run.md`)
- `## Next change I would test`

## How to save the files

The notebooks write to `stage-06/` by default. In Colab they write to Colab's copy of your repo: download
them from the Files panel (and the notebook with File, then Download .ipynb) and commit them here.
Run live (with a key) for numbers you can use. The offline mock (`KIT_OFFLINE=1`) only proves the code runs.
