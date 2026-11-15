# About this example

This is an example finished Stage 10, made with the kit's offline mock model (`KIT_OFFLINE=1`).
The latency, time to first token, cost and quality numbers are made up by the mock, NOT real results.
`data/holdout.csv` is the kit's synthetic A/B test.

You must still do these yourself:

- Run `notebooks/10_tracing.ipynb` against your live app with 20 or more real requests.
- Build `metric-tree.md` from the events YOUR app logs.
- Write the threshold in `10_ab_readout.ipynb` before you run it, and link any code you changed outside `stage-10/`.
