# Stage 15: the take-home, the system design answer, and a portfolio-ready repo

This stage has no notebook. You ship one small feature behind your eval gate, record a system design answer,
and make the repo readable for a hiring manager.

## Checklist: what the grader looks for

| Item | What it is | Start from |
| --- | --- | --- |
| `stage-15/TAKEHOME.md` | the small feature, the exact repo area you changed, the eval gate, the ship or no ship call, the PR link | `templates/TAKEHOME.md` |
| A pull request in your repo | your visible commits, a short description, and at least one number from a real run (pass rate, success count or failure count) copied from the CI run or `make evals` output, not typed by hand | your branch |
| `stage-15/README.md` | four short sections (below), plus the PR link, the live URL, the recording link, and timestamps or a chapter list | this file (replace this checklist) |
| A 25 to 35 minute recording | your system design answer (below) | you |
| Root `README.md` | what it does, who it is for, the live URL, how quality is checked, current limits, where the take-home and recording are | `templates/PORTFOLIO_README.md` |
| A green CI run | a status badge or a link to a passing run on the branch you submit | your `.github/workflows/evals.yml` |

## Your stage-15/README.md

Use these four headings:

1. **Decisions I made**
2. **What I measured**
3. **What the results mean**
4. **What I would do next**

Then add:

- Pull request: <PR link>
- Live URL: <your live URL>
- Recording: <recording link>
- Chapters: one line per chapter, for example `00:00 the product`, `04:30 drill-down 1: retrieval`, `12:00 drill-down 2: eval design`, `20:00 drill-down 3: approval flow`, `28:00 limits and next`

## The recording

25 to 35 minutes. Explain the product end to end: user, data, retrieval, model, guardrails, evals, CI, deployment.
Then three drill-downs on choices someone can see in the repo, such as retrieval, eval design, approval flow, CI,
deployment, prompt design or action safety. Show the file while you talk about it. Upload it anywhere with a
shareable link (YouTube unlisted, Loom, Google Drive).

## Submit

The GitHub repo link, the live URL, and the recording link. The submit box has no "Recording" link type: add the
recording as a second **Live** link. It is also in `stage-15/README.md`.
