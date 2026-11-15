# Stage 5: PRD, ship bar and fallback for one feature

Submit the GitHub link to your repo's `stage-05/` folder plus the live URL of the deployed app.

## Checklist

| File | What the brief asks for | How to make it |
| --- | --- | --- |
| `stage-05/PRD.md` | Feature name, 2 or 3 sentences of context from your Stage 4 note and baseline numbers, the production boundary | copy `PRD.template.md` |
| (same file) | 4 or more named failure modes, each with a user visible symptom and a fallback path; an always, ask first, never guardrail table with your feature's action placed and a reason | `PRD.template.md` |
| (same file) | The ship bar set before any eval: one metric, one number, the dataset; the model tested, what to re-test if it changes, one post launch metric | `PRD.template.md` |
| `stage-05/evals/acceptance.jsonl` | 15 or more executable cases matching the PRD, a mix of normal, edge and failure (`kind`) | start from `evals/acceptance.jsonl` |
| `stage-05/acceptance-run.txt` | The real output of `scripts/acceptance.py` against your live URL, with the score and SHIP or DO NOT SHIP | the command below |
| a fallback in the app | One named failure from the PRD handled in the app | `FALLBACKS` and `fallback()` in `app/app.py` |
| `stage-05/README.md` | Key decisions, how to trigger the fallback on the live app, what was measured, result versus the ship bar, what is out of scope, what you would do next | you, from the template below |

## Run the acceptance cases against your live URL

Streamlit has no POST endpoint, so deploy `app/api.py` (same `answer()`, a question page at `/`, and
`POST /ask`). Steps for Render or Hugging Face Spaces are in `app/README.md`. Submit that URL.

```
python scripts/acceptance.py --bar 0.9 --cases stage-05/evals/acceptance.jsonl \
  --url https://YOUR-APP.onrender.com --out stage-05/acceptance-run.txt
```

The saved file starts with the URL, date, model, cases and ship bar. Do not edit it by hand.
Use `--bar` with the number from your PRD. A run without `--url` tests local code only and does not count.

## Case fields

`kind` (normal, edge, failure), `cite_any`, `never_cite`, `must_contain_any`, `must_not_contain`, and
`expect_fallback` (true, or a fallback name like `no_page`). See the top of `scripts/acceptance.py`.

## The fallback

`app/app.py` has two named fallbacks: `no_page` (no help page matches; trigger it with `zzzz qqqq`) and
`model_error` (the model call fails). Every reply says which fallback fired. Build the one your PRD names:
add it to `FALLBACKS`, return `fallback("<name>")` where it happens, and add an acceptance case with
`expect_fallback` for it.

## README template

```
## Key decisions
## How to trigger the fallback on the live app
## What I measured
(link to acceptance-run.txt)
## Result versus the ship bar
## Out of scope
## What I would do next
```
