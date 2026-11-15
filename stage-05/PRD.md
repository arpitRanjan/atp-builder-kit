# PRD: billing handoff in the Quillnote help assistant

## Context

The help assistant answers how-to questions from the Quillnote help pages. In Stage 4 the free keyword rule
picked the right page in 92 percent of 25 cases against 88 percent for the model
([../stage-04/README.md](../stage-04/README.md), [../stage-04/comparison.md](../stage-04/comparison.md)), so page picking is not the main risk.
The risk is billing: in Stage 2 billing questions ended with a human, and before the Stage 3 fix the app
showed admin refund steps to users.

## Production boundary for this version

For end users of the public help app. It answers how-to questions from public and team help pages and
cites them. It never reads admin pages, never issues refunds or changes an account, and sends every billing
or refund question to Quillnote support. English only.

## Failure modes

| Failure mode | What the user sees | Recovery or fallback |
| --- | --- | --- |
| billing question | a refund or "charged twice" question | `billing_handoff`: a message that sends them to support with their invoice number, no steps |
| no matching page | a question the help pages do not cover | `no_page`: "No help page matches", try other words or contact support |
| model error | the model call fails or times out | `model_error`: try again in a minute, or contact support |
| spend limit reached | many questions from one client in a day | `spend_guard`: HTTP 429 with "try again tomorrow" |
| wrong page cited | an answer that cites an unrelated page | no automatic fallback yet; caught by acceptance cases with `cite_any` |

The fallback built in the app for this version: `billing_handoff` (`app/app.py`, `FALLBACKS` and `BILLING_WORDS`).

## Guardrails

| Always | Ask first | Never |
| --- | --- | --- |
| cite the help page used | change a user's plan | issue a refund |
| send billing questions to support | share a notebook with someone new | show admin only pages to users |
| say when no page answers | | delete user data |

My feature's action, sending a billing question to support, is in **always** because it moves no money and
changes no data; the risky act (a refund) stays with a person.

## Ship bar (set before any eval run)

- Metric: acceptance pass rate.
- Threshold: 0.90 (at most 1 failed case in 18).
- Dataset: `stage-05/evals/acceptance.jsonl` (18 cases: normal 9, edge 5, failure 4).

## Acceptance criteria

1. How-to questions cite the right help page (a01 to a13, a17).
2. Billing and refund questions get `billing_handoff` and never cite admin pages (a14, a16).
3. Questions no page covers get `no_page` with a support path (a15).
4. Admin actions are never shown to users (a18, and `never_cite` in a12, a13, a17).

## Model

- Model or setting tested: `<your model>` (this example: the offline mock model), temperature default, output cap 400, `prompts/help_v2.md`, top 3 pages.
- If it changes, re-test: the full acceptance run against the live URL, and the Stage 3 billing re-test (50 runs).

## After launch

- Metric to watch: share of questions that end in a fallback, by fallback name, read daily from the app logs.
