# Stage 14: lead the room with a cold handoff

This stage has no notebook. You hand the project to someone who has never seen it.

## Checklist: files the grader looks for

| File | What it is | Made by |
| --- | --- | --- |
| `stage-14/README.md` | fresh clone setup and run steps, the exact command `make evals`, where its output lands, the expected outcome, and a section **Decisions, what I measured, and next** | you, from `templates/HANDOFF.md` (replace this checklist) |
| `stage-14/SPEC.md` | the current spec with its production boundary: in scope, out of scope, and where human approval is required before any drafted action | you, from `templates/SPEC.md` and your `stage-05/PRD.md` |
| `stage-14/evals-run.txt` | the raw output of `make evals` | `make evals 2>&1 \| tee stage-14/evals-run.txt` |
| `stage-14/traces/spans.jsonl` | a trace export: every golden case, one JSON line per span | `python stage-14/trace_failures.py` |
| `stage-14/traces/failing-cases.csv` | each failing golden case with its trace id | `python stage-14/trace_failures.py` |
| `stage-14/known-failures.md` | 3 or more current failures or sharp edges, each with a user impact note and a trace link | you, from `templates/KNOWN_FAILURES.md` |
| `stage-14/peer-run-notes.md` | date, who the peer was, every question or blocker, whether they finished, and the README change for each | you, from `templates/PEER_RUN_NOTES.md` |

## Steps

1. Run `make evals 2>&1 | tee stage-14/evals-run.txt` and `python stage-14/trace_failures.py` (add `KIT_OFFLINE=1` in front if you have no key, but use a live run for the numbers in your README).
2. Copy the templates and fill in every `<...>`.
3. Give one peer only the repo link. Write down every question they ask. Fix the README for each one.
4. In your README, say what handoff choices you made, what you measured from the eval run and the peer run, and the single next improvement.

## Submit

The GitHub repo link.
