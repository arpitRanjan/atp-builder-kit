# Procurement pack: help assistant for Northwind Learning (example)

Example made with the offline mock model. Numbers and provider are from that run.

## 1. Can one role see another role's pages? (leak test)

No. Each role ran 16 prompts with its role filter on: student 16 passed, tutor 16 passed, admin 16 passed, 0 failed.
With the filter off, 16 of 16 prompts leaked, so the test can catch a leak. Evidence: [leak-test/summary.md](leak-test/summary.md),
raw results in [leak-test/](leak-test/), the filter in `kit/rag.py` (`chunk_pages(..., access=...)` and `VectorIndex.search(role=...)`).

## 2. What do you keep, for how long, and what is redacted? (retention and redaction)

| Data | Where it is kept | How long | Redaction |
| --- | --- | --- | --- |
| Audit log | [audit-log.jsonl](audit-log.jsonl) | 30 days in the pilot | no raw question or answer text, only ids, pages, model and token counts |
| Answers | [answers.jsonl](answers.jsonl) | practice data only | synthetic questions; real user text is never stored |
| Provider side | `<your provider>` | `<their retention>` | only the question and the retrieved page text are sent |

## 3. Can we see what the agent did? (audit log of agent actions)

Yes. One JSON line per answer: time, action, role, question id, pages retrieved, pages cited, provider, model, tokens.
Evidence: [audit-log.jsonl](audit-log.jsonl), written by `audit()` in step 4 of [the notebook](notebooks/11_customer_deployment.ipynb).

## 4. What does the model provider do with our data? (provider data terms)

Provider and model in this example: `mock` (no data leaves the machine). For a live run: `<provider and model>`, terms at
`<link to the provider's data use page>`. Free tiers may use prompts to improve the provider's products, so the pilot uses
only Northwind's help pages and synthetic questions.

## 5. Do users know they are talking to an AI? (AI disclosure)

The text users see above the chat box: "You are chatting with an AI assistant. It answers only from Northwind help pages
and can be wrong." Where it is set: `DISCLOSURE` in step 4 of [the notebook](notebooks/11_customer_deployment.ipynb).

## Open items

- Retention on the provider side, once a live provider is chosen.
