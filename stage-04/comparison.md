# Baseline vs LLM on the same cases

Assumption: Given a user's question, a model can pick the help page that answers it.
Pass rule: A case passes when the picked page id is one of the case's expected page ids. Bar: 80%.

| method | cases | pass_rate | avg_latency_s | avg_cost_usd |
| --- | --- | --- | --- | --- |
| keyword rule | 25 | 0.92 | 0.0005 | 0.0 |
| LLM mock-model | 25 | 0.88 | 0.6092 | 0.00132 |

Case level results: [baseline_results.csv](baseline_results.csv), [llm_results.csv](llm_results.csv).

**Which method I would use now:** Use the keyword rule now: it passed 92 percent of the 25 cases against 88 percent for the LLM, at no cost and under 1 ms. The LLM costs about $0.0013 per case and was right on only 2 cases the rule missed (q05, q06). Rerun with a real model before paying for the LLM step.
