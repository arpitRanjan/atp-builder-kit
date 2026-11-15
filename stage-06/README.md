# Stage 6: agent loop for drafting bug reports from help questions

Feature from my Stage 5 PRD: answer a Quillnote help question with cited pages, and draft a bug report
when the user asks for one. Built in `06_harness.ipynb` on my own loop with two tools: `search_docs`
(my Stage 3 MCP search tool, `mcp_server/server.py`) and `draft_issue` (a mock tool that only appends
to `outbox.jsonl`). Every step is logged to `traces/run.jsonl`.

## Why this feature needs an agent

The number and order of steps depends on the request. A plain question needs one search and an answer.
A bug report needs a search for related pages, then a draft, then an answer that says what was saved.
A fixed workflow would either always draft (wrong for questions) or never search before drafting.

## Controls I chose and why

All five are in code in `run_agent()`, not in the prompt:

- Step budget: `STEP_BUDGET = 6` model calls. Normal runs need 2 or 3.
- Spend budget: `SPEND_BUDGET_USD = 0.01` per run, checked before each call with an estimate of the next call.
- Capped retry: `MAX_RETRIES = 2` for timeouts and dropped connections only.
- Approval check: `draft_issue` runs only when the task is in `APPROVED`. Otherwise the tool returns DENIED.
- Validated structured output: `validate_final()` checks the final answer against `AgentAnswer` (it must cite
  a page a tool returned, and must not claim a draft that was never saved), with `MAX_VALIDATION_RETRIES = 1`.

## What I measured

10 tasks, 7 configurations, 70 runs (`pass_rates.csv`, `runs.csv`):

| Config | Passed | Failed tasks | Cost (USD) |
| --- | --- | --- | --- |
| all on | 10/10 | none | 0.01969 |
| all off | 5/10 | t05, t07, t08, t09, t10 | 0.03316 |
| no step budget | 10/10 | none | 0.02690 |
| no spend budget | 9/10 | t09 | 0.03189 |
| no capped retry | 9/10 | t08 | 0.01974 |
| no approval check | 9/10 | t07 | 0.01968 |
| no validation | 9/10 | t05 | 0.01940 |

Each control saves one task except the step budget: with it off, the spend budget still stopped the
endless task (t10), but only after 19 steps instead of 6, and that run cost $0.0092 instead of $0.0020.

## What failed

`failed_run.md` walks through run `no-retry-t08` step by step. Failing layer: harness. The search tool
timed out once, nothing retried it, and the user got the fallback instead of an answer.

Context: `context_ablation.csv` shows which probes fail when each block is removed. `compaction_check.csv`
shows the budget constraint ("20 dollars") is lost by the summary and kept once it is pinned.

## Next change I would test

Make the step budget the first stop for runaway loops: lower it to 4 and check that t01 to t08 still pass.
