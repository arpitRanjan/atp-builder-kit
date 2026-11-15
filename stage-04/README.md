# Stage 4: discovery and strategy (EXAMPLE, offline mock model)

Riskiest assumption: given a user's question, a model can pick the help page that answers it, well enough to
be worth its cost over a free keyword rule.

## Decision

Keep the keyword rule as the page picker for now, and use it as the baseline every model change must beat
([comparison.md](comparison.md)).

## What we measured

- 25 labeled cases, pass rule and 80 percent bar written before the run ([04_baseline_vs_llm.ipynb](04_baseline_vs_llm.ipynb), Step 2).
- LLM: 88 percent pass (22 of 25), 0.61 s average latency, $0.00132 average cost per case ([llm_results.csv](llm_results.csv)).
- Keyword rule on the same case ids: 92 percent pass (23 of 25), under 1 ms, $0 ([baseline_results.csv](baseline_results.csv)).
- The assumption holds against the bar (88 percent is over 80 percent), but the free rule is better on these cases ([comparison.md](comparison.md)).

## Chosen model vendor harness

`mock-model-b` + Google Gemini API paid tier + the kit harness (`app/app.py`, keyword search, top 3), score
4.02 of 5 against 3.41 for model A on the free tier ([stack_choice.md](stack_choice.md)). It is cheaper per
task in Stage 1 ([../stage-01/probe_summary.csv](../stage-01/probe_summary.csv)) and its data terms are better for user data,
but its Stage 1 pass rate is lower (68 against 90 percent), so it needs the JSON retry from Stage 1 first.

## What I would do next

1. Rerun Stage 1 and this notebook with real models, then rescore [stack_choice.md](stack_choice.md).
2. Read each vendor's data terms page and write the date in `CANDIDATES`.
3. Add the 5 cases where the two methods disagree to the Stage 5 acceptance set.
