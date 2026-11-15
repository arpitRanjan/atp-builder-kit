# Take-home: <the small feature>

Copy this file to `stage-15/TAKEHOME.md` and fill in every `<...>`. Keep it to one page.

## The product

<Two sentences: your carried product, its user, and what it answers from. Say plainly that all data is synthetic.>

## The small feature I chose

<One feature you can ship in 3 to 4 hours, for example: "rerank the top 3 pages so the answer cites the best one".
Why this one: the failure or user need it fixes, with its evidence (a failing case or a trace id).>

## The exact repo area I changed

| File | What changed |
| --- | --- |
| <`app/app.py`> | <one line> |
| <`evals/golden.jsonl` or a test> | <the case that proves it> |

## The eval gate that approves it

- Gate: <for example: `make evals` hard gates in CI, `.github/workflows/evals.yml`>
- Bar: <for example: 17 of 20 hard gates (85%), set as `--bar 0.85` (`EVAL_BAR`) in `.github/workflows/evals.yml`>
- Result before: <number, from a real run>
- Result after: <number, from a real run, with the CI run link>

## Ship or no ship

**<Ship | No ship>**: <one or two sentences on why, and what is not fixed>.

## Pull request

<link to the pull request in your repo>

## Time box and tools

<How long it took. Which tools you used, AI assistants included, and for what.>
