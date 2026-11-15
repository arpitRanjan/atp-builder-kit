# Example stage 2 (offline mock model)

Made by running `notebooks/02_sql_duckdb.ipynb` and `notebooks/02_traces_pandas.ipynb` offline, with the
Stage 1 example `probe_runs.csv` from `checkpoint/stage-01`. The numbers are not real model results.
The traces are the kit's synthetic traces, and every saved file holds redacted text only.

What a learner must still do themselves:

- Use their own Stage 1 `probe_runs.csv` (real runs), so the `from_stage1_probe` rows are theirs.
- Review every suggested label and record changes in `OVERRIDES`; edit layer guess, severity and how to check the fix.
- Name their own two segments, write their own trap note, README sections and retention table.
- Submit `<your notebook links>` or `<your repo link>/tree/main/stage-02`.
