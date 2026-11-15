# Stage 15: take-home, system design, portfolio (example)

Example skeleton. Every `<...>` is the learner's own work: the PR, the live URL, the recording and its numbers.

- Pull request: `<PR link>`
- Live URL: `<your live URL>`
- Recording (a 25 to 35 minute system design walkthrough): `<recording link>`
- Take-home: [TAKEHOME.md](TAKEHOME.md)
- Portfolio README: the root [README.md](../README.md), started from `templates/PORTFOLIO_README.md`

## Decisions I made

- Picked the admin page leak (stage 14 known failure 1) because it is the one failure with a safety cost.
- Fixed it in the app's search, not in the prompt, so the model never sees an admin page.
- `<more>`

## What I measured

- Hard gates before and after, from the CI runs: `<numbers and links>`
- Admin pages cited across the golden and Spanish sets: `<before> to <after>`

## What the results mean

`<two or three sentences: did it meet the gate, and what it does not fix>`

## What I would do next

`<one thing>`

## Recording chapters

- `00:00` the product end to end: user, pages, retrieval, model, guardrails, evals, CI, deployment
- `<mm:ss>` drill-down 1: `<for example retrieval and the role filter, app/app.py and kit/rag.py>`
- `<mm:ss>` drill-down 2: `<for example eval design, evals/ and the CI workflow>`
- `<mm:ss>` drill-down 3: `<for example approval flow and the host allowlist, kit/guardrails.py>`
- `<mm:ss>` limits and what is next
