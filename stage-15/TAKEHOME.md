# Take-home: keep admin pages out of answers in the app itself

Example. The feature and numbers come from the kit's own Quillnote project and offline mock runs.

## The product

A help assistant for Quillnote, an invented note app. It answers how-to questions from 15 help pages and cites them.
All data is synthetic.

## The small feature I chose

Hide admin pages in the app's own search, so a public user can never get one, in any language. Why this one:
known failure 1 in `stage-14/known-failures.md`: a Spanish question cited the admin page qn-14 (trace `8956d7f10900`).

## The exact repo area I changed

| File | What changed |
| --- | --- |
| `app/app.py` | `HIDE_VISIBILITY = ["admin"]`, so `answer()` drops admin pages before the model sees them |
| `evals/golden.jsonl` | `<one new case: a question that shares words with an admin page, never_cite qn-13,qn-14,qn-15>` |

## The eval gate that approves it

- Gate: `make evals` hard gates in CI (`.github/workflows/evals.yml`) plus `python stage-12/locale_evals.py`.
- Bar: 18 of 20 hard gates or better, and no case cites an admin page.
- Result before: `<from the CI run on main>`
- Result after: `<from the CI run on the pull request, with its link>`

## Ship or no ship

**`<Ship | No ship>`**: `<one or two sentences>`.

## Pull request

`<link to the pull request in your repo>`

## Time box and tools

`<How long it took. Which tools you used, AI assistants included, and for what.>`
