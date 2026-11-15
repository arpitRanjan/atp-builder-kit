# Handoff: Quillnote help assistant (example)

Example filled in from offline mock runs. See `EXAMPLE.md`. Replace every number with your own live run.

The handoff bundle in `stage-14/`:

| File | What it is |
| --- | --- |
| `README.md` | this file |
| [SPEC.md](SPEC.md) | the current spec with its production boundary |
| [traces/spans.jsonl](traces/spans.jsonl) | a trace export: 40 traced requests, one JSON line per span |
| [traces/failing-cases.csv](traces/failing-cases.csv) | every failing case with its trace id |
| [known-failures.md](known-failures.md) | 4 current failures, each with user impact and a trace link |
| [peer-run-notes.md](peer-run-notes.md) | notes from one peer who ran the repo cold |
| [evals-run.txt](evals-run.txt) | the raw output of `make evals` |

## What it does, in two sentences

Quillnote users ask how to use the app; it answers only from the 15 Quillnote help pages and cites them. It may save a
draft bug report to a local outbox, and only after approval.

## Fresh clone setup and run steps

```
git clone https://github.com/<you>/atp-builder-kit && cd atp-builder-kit
python3.11 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env                      # fill in a key, or skip it and put KIT_OFFLINE=1 in front of each command
make test PYTHON=.venv/bin/python          # the offline tests
make evals                                 # the golden set in one command
make evals 2>&1 | tee stage-14/evals-run.txt   # the same, with the raw output saved
python stage-14/trace_failures.py          # traces every golden and Spanish case to stage-14/traces/
```

## Where the results are

- `make evals` prints one line per case and a total, and exits 1 if a hard gate fails. Raw output: [evals-run.txt](evals-run.txt).
- Traces: [traces/spans.jsonl](traces/spans.jsonl) and [traces/failing-cases.csv](traces/failing-cases.csv).

## Expected outcome when the repo is working

The terminal ends with `Hard gates: 20/20 passed` and exit code 0. `trace_failures.py` ends with `25/40 passed`:
the 15 failures are Spanish questions through the app as is (known failure 1 to 3). `streamlit run app/app.py`
opens a help box that answers with cited page ids.

| Check | Result on 2026-11-15, offline mock | Bar |
| --- | --- | --- |
| `make evals` hard gates | 20 of 20 | 18 of 20 |
| Red team pass^3 (stage 13) | 1.00 | 1.00 |

## How it fits together

A question goes to keyword search over `corpus/`, then to the model with the top 3 pages, then through the output
check, then to the user with cited page ids.

| Part | File |
| --- | --- |
| Answer function | `app/app.py` |
| Retrieval and roles | `kit/rag.py` |
| Guardrails | `kit/guardrails.py` |
| Evals | `evals/` |
| Spans | `kit/tracing.py` |

## Decisions, what I measured, and next

- Handoff choices: one command for evals (`make evals`), raw output saved to a file, every golden and Spanish case traced so each known failure links to its own trace, the production boundary written in the spec.
- What I measured: `make evals` 20 of 20 hard gates; traces 25 of 40 cases pass (all 15 fails are Spanish); peer run: `<minutes to green, questions asked, from peer-run-notes.md>`.
- Next improvement to the handoff: `<the one change the peer run points to>`.
