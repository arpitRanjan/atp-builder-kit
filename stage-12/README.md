# Stage 12: locale or multimodal readiness pack

One feature of your product, the help answer, in a second language. The kit supports Spanish end to end.
A multimodal variant (for example a screenshot question) is also allowed by the brief, but the kit has no
image data or code for it: you would build that yourself, with the same files below.

Run `notebooks/12_locale_eval.ipynb`. It writes every file below into `stage-12/`.

## Checklist: files the grader looks for

| File | What it is | Made by |
| --- | --- | --- |
| `stage-12/12_locale_eval.ipynb` | your run, saved with outputs | you: run `notebooks/12_locale_eval.ipynb`, save a copy here |
| `stage-12/locale_evals.py` | the variant feature (`localized_ask`: English search, answer in Spanish) and the CI runner | the kit, change it if you change the variant |
| `stage-12/golden-set.jsonl` | 10 or more cases, each with `input`, `expected` (the page to cite) and `source`. Includes typo cases and mixed language cases (`degradation` column). | notebook step 2, copied from `evals/golden_es.jsonl` the first time; then yours to edit |
| `stage-12/outputs.jsonl` | the real output for every case, as is and with the variant | notebook step 5 |
| `stage-12/results.csv` | pass rates by kind (English, translated, degraded), as is and with the variant | notebook step 5 |
| `stage-12/results/ci-results.json` | the result file CI writes: pass rate, bar, every case | `python stage-12/locale_evals.py` (notebook step 6, and CI) |
| `stage-12/judge-prompt.md` | the one judge criterion and the exact judge prompt | notebook step 7 |
| `stage-12/judge-agreement.md` and `.csv` | agreement on the 10 Spanish hand labels (count and percent) and a table of every disagreement | notebook step 7 |
| `.github/workflows/evals.yml` | your Stage 8 workflow, with its Spanish step kept (see below) | you |
| `stage-12/README.md` | your README (replace this checklist) | you |

## The CI change

You do not need to add a step. `.github/workflows/evals.yml.example` already has the Spanish step.
Keep it when you rename the file to `evals.yml` in Stage 8. It runs only once `stage-12/golden-set.jsonl`
exists. Before that it prints a skip message and passes. After you commit your golden set, it runs on every
pull request:

```
python stage-12/locale_evals.py --bar 0.8 --out stage-12/results/ci-results.json
```

The workflow's last step uploads `stage-12/results/` with the other eval results.

Locally the same thing is: `python stage-12/locale_evals.py` (exit 1 means under the bar).

## Your README must have

1. A short section that names the feature, the target language, why you picked it, and what stayed the same from your Stage 8 eval setup (the hard gates in `evals/gates.py`, the judge prompt, the CI workflow).
2. A results section with: the main metric (variant hard gate pass rate on the golden set), the judge agreement (count and percent), the main failure pattern you saw, and what you would do next.
3. A last line with exactly one readiness call: **ship**, **hold**, or **ship with a named limit** (name the limit).

## Submit

The GitHub folder link to `stage-12/`.

Offline (`KIT_OFFLINE=1`) the translator is a word list and the judge is a word overlap rule. Those numbers only show the notebook works. Run it live for the numbers in your README.
