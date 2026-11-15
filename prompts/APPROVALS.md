# Prompt approvals

Every prompt file in `prompts/` needs one row here. The row names the eval run that approved that exact text.
`python evals/run_evals.py --check-prompts` reads this table. CI runs the same check.

| Prompt | Eval run | Date | Note |
| --- | --- | --- | --- |
| help_v1.md | kit-baseline | 2026-11-15 | Kit baseline, not your run. It approves the kit's own help_v1.md text, unchanged. |

## About the kit baseline row

`kit-baseline` is a special run id. It has no file in `evals/runs/`. It passes only while `help_v1.md` is
the kit's original text, so `--check-prompts` passes on a fresh fork. If you change `help_v1.md`, the check fails.

## How to approve your own prompt

1. Copy `help_v1.md` to `help_v2.md`. Change the copy. Point `PROMPT_FILE` in `app/app.py` at it.
2. Run `python evals/run_evals.py --save` with your real key. It prints a run id, like `20261120T101500Z-1a2b3c`.
   It also writes `evals/runs/<run id>.json`. Commit that file.
3. Add a row: `| help_v2.md | <run id> | <date> | <one line on why> |`.
4. Run `python evals/run_evals.py --check-prompts`. It fails if a prompt has no row, if its run did not pass,
   or if the run was made on different prompt text.
5. For your Stage 8 example, replace the `kit-baseline` row with a real run of `help_v1.md` too.
