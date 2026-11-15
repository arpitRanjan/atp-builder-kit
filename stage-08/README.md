# Stage 8: turn your failure backlog into a real eval gate

Submit: your GitHub repo link, plus the link to one pull request that the eval gate blocked.

This stage lives in the repo paths the product uses, not only in `stage-08/`. Only your notes go in
`stage-08/README.md`.

## Checklist: files in the repo

| Path | What it must show | Made by |
| --- | --- | --- |
| `evals/golden.jsonl` | Cases built from your Stage 2 backlog (`stage-02/failure_backlog.csv`) and your Stage 7 rows (`stage-07/feedback.jsonl`). Every case has `source` (the trace id or feedback row it came from) and `split`: `dev`, `held-out` or `regression` | you, starting from the kit's 20 cases. `kit/feedback.py` `to_golden_case()` turns a feedback row into a case |
| `evals/gates.py` | Two code graders (`citation_failures`, `content_failures`) and one model judge (`judge_verdict`) | the kit; change them to your feature |
| Regression cases | `split: regression` in `evals/golden.jsonl`, with at least one sycophancy flip (kit: g17) and one pressure case (kit: g18). The pass condition is in the case: `cite_any`, `never_cite`, `must_not_contain`, `must_contain_any` | you |
| `evals/run_evals.py` or `evals/promptfooconfig.yaml` | The runnable suite (pytest-free runner or promptfoo) | the kit |
| `notebooks/08_judge_calibration.ipynb` | Your executed run, against YOUR labels in `evals/labels.csv` (keep the `split` column). It prints the true positive and true negative rates, and saves `stage-08/judge_calibration.json` | your run of the notebook, committed at that path |
| `.github/workflows/evals.yml` | Runs the suite on every pull request: rename `evals.yml.example` | you |
| `prompts/help_vN.md` and `prompts/APPROVALS.md` | Each prompt version names the eval run that approved it (see below) | you |
| `evals/runs/<run id>.json` | The saved eval run each approval points to. It also keeps every case's question, reference answer and model answer, with an empty `label` field, so you can hand label rows from a real run | `python evals/run_evals.py --save` |
| `stage-08/README.md` | The sections below | you |

## How to approve a prompt version

`prompts/APPROVALS.md` ships with one row: `help_v1.md` approved by `kit-baseline`. That row is the kit's
baseline, not a real run. It passes only while `help_v1.md` is unchanged. Replace it with your own run.

1. Copy `prompts/help_v1.md` to `help_v2.md`, change the copy, point `PROMPT_FILE` in `app/app.py` at it.
2. Run `python evals/run_evals.py --save`. It prints a run id and writes `evals/runs/<run id>.json`,
   which records the prompt file and a hash of its text.
3. Add a row to `prompts/APPROVALS.md`: `| help_v2.md | <run id> | <date> | <one line on why> |`
   (header: `| Prompt | Eval run | Date | Note |`).
4. `python evals/run_evals.py --check-prompts` fails if any prompt has no row, if the run did not pass,
   or if the run was made on different prompt text. The CI workflow runs this check too.

## The pass bar

`python evals/run_evals.py --bar 0.85` passes when at least 85% of cases pass the hard gates. With no `--bar`,
it uses the `EVAL_BAR` environment variable, else 0.85. Use `--bar 1` to make every case pass.
`--labels-out evals/to_label.csv` writes every case of the run in the `evals/labels.csv` shape, with empty
`human_label` and `note` columns. Label them by hand, then add the rows to `evals/labels.csv` for the judge notebook. The workflow sets the bar once, in `EVAL_BAR`, and promptfoo uses the same number
(`PROMPTFOO_PASS_RATE_THRESHOLD`). Pick your own bar and write why in this README.

## How to get a blocked pull request

1. Rename `.github/workflows/evals.yml.example` to `evals.yml` and merge it to `main`.
2. In Settings, Branches, add a rule for `main` that requires the `golden-set` check to pass.
3. Open a pull request that pushes the pass rate under your bar, for example a prompt that drops citations.
   One new failing case may stay above an 85% bar. The check goes red and the merge is blocked.
4. Fix it (or close it) and put the pull request link in this README.

## The judge

The judge is advisory until you trust it. Set `JUDGE_HARD=1` (a repository variable or in the workflow)
once its held-out true positive and true negative rates in `stage-08/judge_calibration.json` are high enough.

## README.md sections (use these headings)

- `## How I built the golden set` (from the Stage 2 backlog and the Stage 7 rows)
- `## Dev and held-out split rule`
- `## What I measured` and `## Current results` (include the judge's true positive and true negative rates)
- `## Blind spots`
- `## Blocked pull request` (the link)
- `## Prompt approval example` (one prompt file and the eval run that approved it)
- `## What I would do next`
