# Stage 2: a ranked failure backlog from your traces

Submit a notebook link or the GitHub repo folder for `stage-02/`. If you have no repo yet (the fork comes
in Chapter 3), submit links to both notebooks and keep the README sections in Step 13 of the trace notebook.

## Checklist

| File in `stage-02/` | What the brief asks for | Made by |
| --- | --- | --- |
| `02_sql_duckdb.ipynb` | Five queries with real outputs, and the planted trap: wrong number first, corrected number after, and a note on the cause | `notebooks/02_sql_duckdb.ipynb` (queries in Steps 3 to 7, trap in Step 8) |
| `02_traces_pandas.ipynb` | Load and clean traces in pandas; failure rate for two named segments with numerator and denominator | `notebooks/02_traces_pandas.ipynb`, Steps 2 to 4 |
| (same notebook) | A named failure taxonomy, and two labeled samples: random 30 and stratified 30 | Steps 5 and 6 |
| (same notebook) | A PII redaction pass on the sampled traces, with caught and missed counts | Steps 7 and 8 |
| `labeled_random_30.csv`, `labeled_stratified_30.csv` | The two labeled samples, redacted text only | Step 9 |
| `failure_backlog.csv` | Ranked rows with trace_ids, failure label, layer guess, severity, how to check the fix, and a `from_stage1_probe` column | Steps 10 to 12 |
| `README.md` | Sections **Decisions**, **What I measured**, **What I would do next**, and a retention and access table | you, from the template below |

## Add your Stage 1 probe failures

Step 11 reads your `stage-01/probe_runs.csv` (written by `01_probe_set`). In Colab, upload that file next to
the notebook. Each failed probe becomes a backlog row with `from_stage1_probe = yes`.

## Labels and PII

- `suggest_label` is only a starting rule. Read every sampled row and put your corrections in `OVERRIDES`.
- `layer_guess`, `severity` and `how_to_check_fix` start from the taxonomy. Edit any you disagree with.
- Only redacted text is saved. A row whose redaction misses true PII is saved as `[WITHHELD: redaction missed PII]`.
  Never commit raw trace text.

## README template (replace the checklist above with this, filled in)

```
## Decisions
## What I measured
## What I would do next
## Retention and access
| Where traces live | What is stored | How long I keep it | Who can access it | How it is deleted or cleared |
| --- | --- | --- | --- | --- |
| data/traces.jsonl in the kit | | | | |
| the notebook runtime (Colab or local) | | | | |
| stage-02/*.csv in my GitHub repo | | | | |
| stage-01/probe_runs.csv | | | | |
| the model provider's logs | | | | |
```

Add a row for every other place your traces live.
