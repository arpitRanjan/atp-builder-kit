# Stage 5: PRD, ship bar and fallback (EXAMPLE, offline mock model)

Live URL: `<your live URL>`. PRD: [PRD.md](PRD.md). Cases: [evals/acceptance.jsonl](evals/acceptance.jsonl).
Run output: [acceptance-run.txt](acceptance-run.txt).

## Key decisions

- One feature: the billing handoff. Billing questions go to a person; the assistant never gives refund steps.
- Ship bar set before the run: 0.90 pass rate on 18 acceptance cases (normal 9, edge 5, failure 4).
- The handoff is a rule on billing words, not a model call, so it costs nothing and cannot be talked out of it.

## How to trigger the fallback on the live app

Ask "I was charged twice, can you refund me?". The reply sends you to support, and the page shows
"Fallback used: billing_handoff". Ask "zzzz qqqq" to see the `no_page` fallback.

## What I measured

`python scripts/acceptance.py --bar 0.9 --cases stage-05/evals/acceptance.jsonl --url <your live URL> --out stage-05/acceptance-run.txt`

## Result versus the ship bar

18 of 18 cases passed (100 percent) against a bar of 90 percent: SHIP. In this example the run was against
the endpoint served locally with the mock model, not a live URL, so it does not count yet.

## Out of scope

Refunds, plan changes, admin pages, languages other than English, and picking a better page than the keyword search.

## What I would do next

If ready to ship: deploy, rerun the acceptance cases against the live URL, and watch the fallback share daily.
If not: add the failing cases to the set, fix the cause, and rerun before deploying again.
