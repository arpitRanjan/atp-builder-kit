# Stage 10: tracing, cost and an A/B readout

Put here:

- `10_tracing.ipynb`: your run of `notebooks/10_tracing.ipynb`, with p50 and p95 latency, time to first token, cost per request and per successful task, and the span that drives spend.
- `traces/spans.jsonl`: the span file the notebook writes (one JSON line per span).
- `10_cost_levers.ipynb`: your run of `notebooks/10_cost_levers.ipynb`, with the cache hit and miss and the cascade log.
- `10_ab_readout.ipynb`: your run of `notebooks/10_ab_readout.ipynb`.
- `ab_threshold.json` and `ab_readout.md`: the rule you set before the analysis, and the decision.
