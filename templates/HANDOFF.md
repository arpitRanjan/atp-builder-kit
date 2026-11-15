# Handoff: <your app name>

Copy this file to `stage-14/README.md` and fill in every `<...>`. The reader has never seen this project.
They should be able to run everything below cold, in under 30 minutes, without asking you.

The handoff bundle in `stage-14/`:

| File | What it is | Start from |
| --- | --- | --- |
| `README.md` | this file: what it does, run steps, expected results, decisions | `templates/HANDOFF.md` |
| `SPEC.md` | the current spec with its production boundary | `templates/SPEC.md` (or your `stage-05/PRD.md`) |
| `traces/spans.jsonl` | at least one trace export | `python stage-14/trace_failures.py` |
| `known-failures.md` | 3 or more current failures, each with user impact and a trace link | `templates/KNOWN_FAILURES.md` |
| `peer-run-notes.md` | notes from one peer who ran the repo cold | `templates/PEER_RUN_NOTES.md` |
| `evals-run.txt` | the raw output of `make evals` | the command below |

## What it does, in two sentences

<Who uses it, what they ask, what it answers from, and what it may do (tools).>

## Fresh clone setup and run steps

```
git clone <your fork URL> && cd atp-builder-kit
python3.11 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env                      # fill in a key, or skip it and put KIT_OFFLINE=1 in front of each command
make test PYTHON=.venv/bin/python          # the offline tests
make evals                                 # the golden set in one command
make evals 2>&1 | tee stage-14/evals-run.txt   # the same, with the raw output saved
python stage-14/trace_failures.py          # traces every golden case to stage-14/traces/
```

## Where the results are

- `make evals` prints one line per case and a total, and exits 1 if a hard gate fails. Raw output: `stage-14/evals-run.txt`.
- Traces: `stage-14/traces/spans.jsonl` (one JSON line per span) and `stage-14/traces/failing-cases.csv` (failing case to trace id).

## Expected outcome when the repo is working

<What the terminal shows, for example: "Hard gates: 17/20 passed", exit code 1 because of the 3 known failures in
known-failures.md. What the app shows: `streamlit run app/app.py` opens a help box that answers with cited page ids.>

| Check | Result on <date>, <provider and model> | Bar |
| --- | --- | --- |
| `make evals` hard gates | <17 of 20> | <18 of 20> |
| p95 latency (from `make traces`) | <ms> | <ms> |
| Red team pass^3 (stage 13) | <1.00> | <1.00> |

## How it fits together

<One paragraph: question, retrieval with the role filter, model, output check, answer. Name the files.>

| Part | File |
| --- | --- |
| Answer function | `app/app.py` |
| Retrieval and roles | `kit/rag.py` |
| Guardrails | `kit/guardrails.py` |
| Evals | `evals/` |
| Spans | `kit/tracing.py` |

## Decisions, what I measured, and next

- Handoff choices I made: <for example: one command for evals, traces per golden case, known failures linked to traces>
- What I measured: <from the real eval run (pass count) and the peer run (time to green, questions asked)>
- The single next improvement to the handoff: <one thing>
