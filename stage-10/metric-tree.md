# Metric tree

Built only from events the app logs: spans in `stage-10/traces/spans.jsonl` (written by `kit/tracing.py`),
feedback rows in `stage-07/feedback.jsonl` and approval rows in `stage-07/approvals.jsonl`.

```
North star: weekly successful help answers
├── Input 1: answer rate (request has a cited page)
├── Input 2: thumbs-down rate
├── Input 3: draft approval rate
├── Input 4: fallback rate
└── Guardrails: cost per successful task, p95 request latency
```

| Metric | Type | Event counted | Denominator | Window | Source file |
| --- | --- | --- | --- | --- | --- |
| Weekly successful help answers | north star | `request` spans with status ok and at least one page in `attrs.cited`, minus requests whose answer got a `thumbs_down` row | none, a count | 7 days, Monday to Sunday UTC | spans.jsonl, feedback.jsonl |
| Answer rate | input | `request` spans with at least one page in `attrs.cited` | all `request` spans | 7 days | spans.jsonl |
| Thumbs-down rate | input | feedback rows with `signal` = thumbs_down | all `request` spans | 7 days | feedback.jsonl, spans.jsonl |
| Draft approval rate | input | approval rows with `outcome` = approve or edit | all approval rows | 7 days | approvals.jsonl |
| Fallback rate | input | `request` spans whose answer was a fallback (no page cited) | all `request` spans | 7 days | spans.jsonl |
| Cost per successful task | guardrail | sum of `cost_usd` over all spans | successful requests (the north star count) | 7 days | spans.jsonl |
| p95 request latency | guardrail | `latency_ms` of `request` spans, 95th percentile | all `request` spans | 7 days | spans.jsonl |

Why each input moves the north star:

- Answer rate: more requests that end with a cited page are more chances for a successful answer.
- Thumbs-down rate: each thumbs down removes one answer from the north star count.
- Draft approval rate: a draft that is rejected means the user's bug report task failed.
- Fallback rate: a fallback is a request that ended without an answer.

Guardrail limits: cost per successful task under $0.001, and p95 request latency under 2,000 ms.
This week (mock run, 20 requests): cost per successful task $0.000604, p95 latency 971 ms.
