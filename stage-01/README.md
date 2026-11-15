# Stage 1: baseline runs and failure predictions

No repo is needed yet. You submit **two notebook links** (Colab shared so anyone with the link can view,
or the notebooks on GitHub or a Gist). When you fork the kit in Chapter 3, move them into this folder.

## Checklist

| What the brief asks for | Where it is made |
| --- | --- |
| Notebook 1: 10 real calls with a hand set system prompt, temperature and output cap | `notebooks/01_first_calls.ipynb`, Steps 3 and 4 |
| A usage table with 10 rows: input tokens, output tokens, stop reason, latency, cost | Step 5 (also saved as `stage-01/usage.csv`) |
| One row with a forced truncation caused by your output cap | call 10 uses `TRUNCATE_CAP`; Step 6 shows the row |
| The key from Colab secrets or an environment variable, never in a cell or output | Step 2 (Colab: key icon, add `GEMINI_API_KEY`) |
| Notebook 2: 10 probe tasks, each with a pass criterion written before any run | `notebooks/01_probe_set.ipynb`, Steps 3 and 4 (edit `data/probes.csv`) |
| Each task run 5 times on 2 models | Step 5 (saved as `stage-01/probe_runs.csv`) |
| Pass rate, cost per task and median latency per model | Step 7 (saved as `stage-01/probe_summary.csv`) |
| Five predicted weaknesses, each tied to model, context, harness or surface; one disproved and rewritten narrower | Step 9 table, in the probe set notebook |
| A short README section: decisions, what you measured, what you would do next | Step 10, in the probe set notebook |

## Files to keep for later stages

- `probe_runs.csv`: Stage 2 adds your failed probes to its failure backlog.
- `probe_summary.csv`: Stage 4 scores models with your numbers.

In Colab, download both from the Files panel before the runtime ends.

## Before you submit

- Run with your real key. If a notebook prints the mock model warning, its numbers are not real runs.
- Rewrite the 10 probes for your own product's help job before you run them.
- Fill in Steps 9 and 10 in your own words, with numbers from the tables above them.
