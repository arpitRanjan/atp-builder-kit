# Stage 3: first working assistant (EXAMPLE, offline mock model)

Live app: `<your live URL>` (see [DEPLOYED.md](DEPLOYED.md)).

## The Stage 2 failure I fixed

Rank 9 in `stage-02/failure_backlog.csv`, label `escalated_billing`: billing and refund questions end with a
human. When I asked the app billing questions, it cited `qn-13` "Refund a double charge", an admin only page,
and showed users the admin refund steps.

## Why this one

It is high severity: money is involved, and users were shown steps they cannot do and should not see.
It is also cheap to fix and easy to check with a clear pass rule.

## What I changed

- `app/app.py`: `HIDE_VISIBILITY = ["admin"]`, so the app never reads admin pages. PR: `<PR link 1>`
- `prompts/help_v2.md`: a new prompt version that never gives admin steps and sends billing problems to support. PR: `<PR link 2>`
- `mcp_server/server.py`: a rewritten `search_docs` description ([MCP.md](MCP.md)). PR: `<PR link 3>`
- `scripts/call_model.py`: an AI assisted change and a debug fix ([DEBUG.md](DEBUG.md)).

## What I measured

The same 10 billing inputs x 5 runs = 50 runs, before and after the fix, with the pass rule written first:
a run passes when the answer cites no admin only page (qn-13, qn-14, qn-15).

- Before: [evals/before/retest_summary.md](evals/before/retest_summary.md), [results](evals/before/retest_results.csv)
- After: [evals/retest_summary.md](evals/retest_summary.md), [results](evals/retest_results.csv), inputs in [evals/retest_inputs.jsonl](evals/retest_inputs.jsonl)

## Result

Before: 5 of 50 runs passed (10 percent). After: 50 of 50 passed (100 percent).

## Next two improvements

1. Billing answers now cite unrelated public pages (for example `qn-07` for "Why was I charged twice?").
   Add a billing fallback that hands the user to support instead (Stage 5).
2. Replace the keyword search with better retrieval, so answers cite the right page, not just a safe one.

## Evidence files

[CODEMAP.md](CODEMAP.md), [DEBUG.md](DEBUG.md), [MCP.md](MCP.md), [PRS.md](PRS.md), [DEPLOYED.md](DEPLOYED.md), [evals/](evals/).
