# Stage 8: evals you can trust

Put here:

- `08_judge_calibration.ipynb`: your run of `notebooks/08_judge_calibration.ipynb`, with the held-out confusion matrix.
- `labels.csv`: your human labels (start from `evals/labels.csv`), with the `split` column kept.
- `golden.jsonl` and `promptfooconfig.yaml`: your golden set and gates (start from `evals/`).
- `.github/workflows/evals.yml`: the renamed `evals.yml.example`, plus a link to one pull request where it ran.
