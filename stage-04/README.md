# Stage 4: discovery and strategy

Submit the GitHub repo folder link to `stage-04/` in your fork.

## Checklist

| File in `stage-04/` | What the brief asks for | Made by |
| --- | --- | --- |
| `04_baseline_vs_llm.ipynb` | Your run, with the pass rule written before the run (Step 2) and your own edited cells | `notebooks/04_baseline_vs_llm.ipynb` |
| `llm_results.csv` | 20 or more cases: case id, input, expected result, pass rule, system output, pass or fail, latency, cost | Step 6 |
| `baseline_results.csv` | The non LLM baseline (keyword rule) on the same case ids: pass or fail, latency, cost | Step 6 |
| `comparison.md` (and `.csv`) | One table: pass rate, average latency, average cost for both methods; which you would use now and why in 3 sentences or less, with links | Step 7 (write `RECOMMENDATION`) |
| `stack_choice.md` | 2 or more model + vendor + harness combinations scored with your Stage 1 numbers and each vendor's data terms, a dated note per vendor, links to the Stage 1 files | Step 9 (edit `CANDIDATES`) |
| `README.md` | The riskiest assumption in one sentence, and a strategy note with the headings below | you, from the template below |

Step 9 reads `stage-01/probe_summary.csv`. In Colab, upload it next to the notebook.

## Show your own work

The grader looks for your changes beyond the kit: your own assumption and cases, an edited baseline,
your own candidates and data terms notes. Commit each change, so it shows in your repo history.

## README template

Every claim must link to a file in the repo.

```
Riskiest assumption: <one sentence>

## Decision
## What we measured
(link to llm_results.csv, baseline_results.csv, comparison.md)
## Chosen model vendor harness
(link to stack_choice.md and the Stage 1 files it used)
## What I would do next
```
