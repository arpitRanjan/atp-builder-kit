# Stage 10: prove it paid off

Submit: the GitHub link to your repo's `stage-10/` folder.

## Checklist: files in stage-10/

| File | What it must show | Made by |
| --- | --- | --- |
| `10_tracing.ipynb` | 20 or more requests through the app, one trace each | your run of `notebooks/10_tracing.ipynb` |
| `traces/spans.jsonl` | One JSON line per span (request, retrieval, model_call, tool_call) | `10_tracing` |
| `tracing_summary.json` | p50 and p95 latency, time to first token, cost per request, cost per successful task, the span that drives the most spend | `10_tracing`, step 7 |
| `span_costs.csv` | Spend by span name | `10_tracing`, step 7 |
| `10_cost_levers.ipynb` | Prompt caching and a cascade on one shared history | your run of `notebooks/10_cost_levers.ipynb` |
| `cost_lever.csv` | Baseline vs lever on the same 10 turn workload: request count, total cost, cost per request, the quality check | `10_cost_levers`, step 8 |
| `metric-tree.md` | One north star, 3 to 5 inputs, 2 guardrails, built only from events your app logs. For every rate: the event, the denominator and the window | you, from `metric-tree-template.md` |
| `10_ab_readout.ipynb` | The holdout readout | your run of `notebooks/10_ab_readout.ipynb` |
| `ab_threshold.json` | The decision rule, written before the analysis (with its time) | `10_ab_readout`, step 2 |
| `ab_readout.md` | Lift, 95 percent interval, n per arm, the mix-shift check, the decision against the threshold | `10_ab_readout`, step 7 |
| `README.md` | The "Decision readout" section below | you |

`python -m kit.tracing --requests 20 --out stage-10/traces/spans.jsonl` sends the same 20 traced requests
without a notebook. (`make traces` writes to `traces/` at the repo root, which git ignores.)

## README.md section (use this heading)

`## Decision readout`, in a few lines:

- What I measured in Stage 10
- The A/B decision threshold I set before the analysis (from `ab_threshold.json`)
- The main decision I made after the analysis
- The single next step I would take

Then link any code you changed outside `stage-10/` (tracing, logging, app changes) so a reviewer can find it.
