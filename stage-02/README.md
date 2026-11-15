# Stage 2: ranked failure backlog (EXAMPLE, offline mock model)

Notebooks: [02_sql_duckdb.ipynb](02_sql_duckdb.ipynb), [02_traces_pandas.ipynb](02_traces_pandas.ipynb).
Files: [failure_backlog.csv](failure_backlog.csv), [labeled_random_30.csv](labeled_random_30.csv),
[labeled_stratified_30.csv](labeled_stratified_30.csv). Stage 1 input: `stage-01/probe_runs.csv`.

## Decisions

- I name two segments: **team plan on android** and **all other traffic**. The team android cohort fails far more often, so its error replies are rank 1 in the backlog.
- I use a taxonomy of five trace labels (ok, error_reply, escalated_billing, escalated_no_answer, slow_answer) and three probe labels for my Stage 1 failures.
- I fix the billing escalations next (rank 9, `escalated_billing`): a money question that reaches a human is high severity, and the help pages hold an admin only refund page that users must never be shown.
- I save only redacted text. The first regex pass missed phone numbers with dots and spelled out emails, so I added two patterns before saving anything.

## What I measured

- DuckDB planted trap: joining events to every `users` row gave 14,348 events; one row per user gives 11,462, the true count. 189 extra plan rows caused the fan out.
- Failure rate, team plan on android: 38 failed of 66 traces (57.6 percent). All other traffic: 54 failed of 493 (11.0 percent). 559 traces after removing 15 duplicates, 12 empty outputs and 29 test users.
- Labeled samples: random 30 and stratified 30 (10 per plan), 59 distinct traces.
- PII on the sampled traces: first pass caught 34 of 48 planted values and missed 14; second pass caught 48 and missed 0. On all 559 traces the second pass caught 407 and missed 0.
- Backlog: 32 ranked rows, 8 of them from my own Stage 1 probe failures (`from_stage1_probe = yes`).

## What I would do next

- Fix rank 9 (billing) in Stage 3 and re-test it with 10 billing questions x 5 runs.
- Find out why team android traces fail: replay rank 1 traces once tracing is in place.
- Review every suggested label by hand and record changes in `OVERRIDES`.

## Retention and access

| Where traces live | What is stored | How long I keep it | Who can access it | How it is deleted or cleared |
| --- | --- | --- | --- | --- |
| `data/traces.jsonl` in the kit | synthetic traces with planted fake PII | as long as the kit repo exists | anyone, the kit is public | not mine to delete; never copy it with real data |
| the notebook runtime (Colab or local) | raw traces loaded in memory, raw text in cell outputs | one session | me | Colab: Runtime, Disconnect and delete runtime; clear outputs before sharing |
| `stage-02/*.csv` in my GitHub repo | redacted messages, labels, trace ids | until the course ends, then 90 days | anyone, the repo is public | delete the files and rewrite history if anything raw slips in |
| `stage-01/probe_runs.csv` | probe prompts and model answers, no user data | until the course ends | anyone, the repo is public | delete the file |
| the model provider's logs | prompts and answers sent in Stage 1 | the provider's retention period | the provider | check the provider's terms; free tier data may be kept and used |
