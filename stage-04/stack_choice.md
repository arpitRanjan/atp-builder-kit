# Scored choice: model + vendor + harness

Weights: {'quality': 0.4, 'cost': 0.2, 'latency': 0.2, 'data_terms': 0.2}. Quality = Stage 1 pass rate x 5. Cost and latency = 5 x best / this one. Data terms = my 1 to 5 score.
Stage 1 numbers from: [stage-01/probe_summary.csv](../stage-01/probe_summary.csv) and [stage-01/probe_runs.csv](../stage-01/probe_runs.csv)

| Candidate | Stage 1 pass rate | Cost per task (USD) | Median latency (s) | Data terms (1 to 5) | Score out of 5 |
| --- | --- | --- | --- | --- | --- |
| mock-model-b + Google Gemini API paid tier + kit harness (app/app.py, keyword search, top 3) | 0.68 | 0.000032 | 0.594 | 4 | 4.02 |
| mock-model-a + Google Gemini API free tier + kit harness (app/app.py, keyword search, top 3) | 0.90 | 0.000155 | 0.512 | 2 | 3.41 |

## Data terms notes

- mock-model-a + Google Gemini API free tier + kit harness (app/app.py, keyword search, top 3): read on <date you read the page>, https://ai.google.dev/gemini-api/terms. Example: on the free tier Google may use prompts and answers to improve its products.
- mock-model-b + Google Gemini API paid tier + kit harness (app/app.py, keyword search, top 3): read on <date you read the page>, https://ai.google.dev/gemini-api/terms. Example: on the paid tier Google says prompts are not used to improve its products.

**Chosen:** mock-model-b + Google Gemini API paid tier + kit harness (app/app.py, keyword search, top 3)
