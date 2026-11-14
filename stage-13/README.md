# Stage 13: guardrails and red team

Put here:

- `13_guardrails.ipynb`: your run of `notebooks/13_guardrails.ipynb`, with the false refusal rate and the added latency.
- `13_injection_and_redteam.ipynb`: your run of `notebooks/13_injection_and_redteam.ipynb`: the injection result before and after your defense, the blocked call, pass^3, and the failover gap.
- `blocked_calls.jsonl` and `redteam_runs.csv`: what the notebook logged.
- Your new attacks go in `evals/regression.jsonl` (the notebook adds them), so every later change is tested against them.
