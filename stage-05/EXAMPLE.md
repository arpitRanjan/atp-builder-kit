# Example stage 5 (offline mock model)

`acceptance-run.txt` is a real run of `scripts/acceptance.py --url` against `app/api.py`, served on
`http://127.0.0.1:8765` with the offline mock model and this example's `app/app.py`. It is NOT a run against
a live URL, and its numbers are not real model results.

Files outside `stage-05/` in this example: `app/app.py` (the `billing_handoff` fallback, on top of the
Stage 3 example fix) and `prompts/help_v2.md` (from Stage 3).

What a learner must still do themselves:

- Write their own PRD for one feature, with their own Stage 4 numbers and a ship bar set before any run.
- Write 15 or more cases for that feature, a mix of normal, edge and failure.
- Build their own named fallback in the app.
- Deploy `app/api.py` (see `app/README.md`) and rerun the acceptance cases against `<your live URL>` with `--out stage-05/acceptance-run.txt`.
- Submit `<your repo link>/tree/main/stage-05` and `<your live URL>`.
