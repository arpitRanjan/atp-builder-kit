# Example stage 14

Made with the offline mock model (`KIT_OFFLINE=1`). The numbers are not real model results.
`evals-run.txt` is the real output of `KIT_OFFLINE=1 make evals`, and `traces/` came from
`KIT_OFFLINE=1 python stage-14/trace_failures.py`. The README, spec and known failures were written by hand from those runs.

You still have to do yourself:
- run `make evals` and `trace_failures.py` live, and replace every number and trace id
- the peer cold run: `peer-run-notes.md` is only a placeholder
- the README changes from the peer's questions
