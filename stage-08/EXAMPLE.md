# About this example

This is an example finished Stage 8, made with the kit's offline mock model (`KIT_OFFLINE=1`).
The eval results, the run record and the judge rates are mock runs, NOT real model results.
The golden set sources point at the kit's synthetic traces; use your own Stage 2 and Stage 7 rows.

Files outside `stage-08/` are at their repo paths: `evals/golden.jsonl`, `evals/labels.csv`,
`evals/runs/`, `prompts/help_v1.md`, `prompts/APPROVALS.md`, `notebooks/08_judge_calibration.ipynb`
and `.github/workflows/evals.yml`.

You must still do these yourself:

- Put `<your repo URL>` and `<your blocked PR link>` in the README: open a real pull request that the
  `golden-set` check blocks.
- Label your own answers in `evals/labels.csv` and re-run the judge calibration live.
- Re-run `python evals/run_evals.py --save` live and approve your prompt with that run id.
