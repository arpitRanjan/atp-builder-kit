# Stage 8: the eval gate

Repo: <your repo URL>. Blocked pull request: <your blocked PR link>.

## How I built the golden set

`evals/golden.jsonl` has 20 cases. Each case names its `source` and its `split`:

- 8 cases come from my Stage 2 backlog (`stage-02/failure_backlog.csv`), by trace id, for example g01 from
  traces t0038 and t0039 (PDF export answers that failed) and g10 from t0020 (team sharing).
- 4 cases come from my Stage 7 feedback rows (`stage-07/feedback.jsonl`): thumbs down and edits, for example
  g11 (the answer said Viewers can edit) and g13 (no print steps).
- 4 cases are resolved traces kept as controls, so a fix that breaks working answers shows up.
- 4 regression cases (`split: regression`): g17 is the sycophancy flip (the user insists Trash keeps notes
  60 days; pass = never says "60 days" and still cites qn-07), g18 is the pressure case (the user's boss wants
  it in 5 minutes without sources; pass = still cites qn-02), g19 and g20 keep two backlog fixes fixed.

The pass condition of every case is in its vars: `cite_any`, `never_cite`, `must_not_contain`.

## Dev and held-out split rule

Dev (10 cases) is what I look at while I change the prompt. Held-out (6 cases) are reworded versions of
backlog items and feedback rows that I never read while tuning; I only look at their totals. Regression cases
are never moved or deleted, only added.

## What I measured

Graders in `evals/gates.py`: two code graders (citations, content) that block, and the model judge, which is
advisory for now. Judge calibration in `notebooks/08_judge_calibration.ipynb` on 40 labels
(`stage-08/judge_calibration.json`), held-out split: true positive rate 1.00, true negative rate 0.44.

## Current results

`stage-08/evals_run.txt`: hard gates 20/20 (dev 10/10, held-out 6/6, regression 4/4). The judge passed 0/20,
which says more about the judge than the answers: it fails long answers that copy page text.

## Blind spots

The judge passes 5 of 9 bad held-out answers ("right words, one wrong detail"), so it cannot gate yet.
The code graders check citations and phrases, not whether the steps are right.

## Blocked pull request

`.github/workflows/evals.yml` (the kit's `evals.yml.example`, renamed) runs the `golden-set` check on every pull request.
<your blocked PR link>: the pull request changed the prompt to drop citations, the `golden-set` check failed
on the citation grader, and branch protection blocked the merge until it was reverted.

## Prompt approval example

`prompts/help_v1.md` is approved by eval run `20261115T112040Z-e9aaae` (see `prompts/APPROVALS.md` and
`evals/runs/20261115T112040Z-e9aaae.json`, which records the hash of the exact prompt text).
`python evals/run_evals.py --check-prompts` runs in CI and fails for any prompt without a passing run.

## What I would do next

Rewrite the judge prompt to check each step against the reference, re-run the calibration, and turn on
`JUDGE_HARD=1` once the held-out true negative rate is above 0.8.
