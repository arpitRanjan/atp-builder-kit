# Metric tree (template)

Copy this file to `stage-10/metric-tree.md` and fill it in. Use ONLY events your app really logs.
The kit app logs these, so you can start from them:

| Event | Where it is logged | Fields you can count |
| --- | --- | --- |
| `request` span | `stage-10/traces/spans.jsonl` | status, latency_ms, cost_usd, attrs.cited |
| `model_call`, `retrieval`, `tool_call` spans | `stage-10/traces/spans.jsonl` | cost_usd, latency_ms, attrs.tool |
| feedback row | `stage-07/feedback.jsonl` | signal (thumbs_down, thumbs_up, edit) |
| approval row | `stage-07/approvals.jsonl` | outcome (approve, edit, reject) |

Rules: exactly one north star, three to five inputs, two guardrails. For every rate, name the event counted,
the denominator and the window.

```
North star: <name>
├── Input 1: <name>
├── Input 2: <name>
├── Input 3: <name>
└── Guardrails: <guardrail 1>, <guardrail 2>
```

| Metric | Type | Event counted | Denominator | Window | Source file |
| --- | --- | --- | --- | --- | --- |
| <north star> | north star | <event> | <denominator, or "none, a count"> | <for example 7 days> | <file> |
| <input 1> | input | | | | |
| <input 2> | input | | | | |
| <input 3> | input | | | | |
| <guardrail 1> | guardrail | | | | |
| <guardrail 2> | guardrail | | | | |

Why each input moves the north star (one line each):

- <input 1>:
- <input 2>:
- <input 3>:
