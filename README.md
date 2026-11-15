# AllthingsPM builder kit

A starter repo for the AllthingsPM AI product management course. You fork it once and build ONE project
in it, stage by stage. The lessons do the teaching; this kit gives you working code, synthetic data and
tests so you can spend your time on product decisions, not setup.

## 1. When to fork

Chapters 1 and 2 need no GitHub account: open the notebooks straight from the links in section 3, run them in Colab, and save your copy to your Google Drive (File, then Save a copy in Drive).

In Chapter 3 you fork the kit: click **Fork** on GitHub, and your copy lives at `https://github.com/<you>/atp-builder-kit`. Move your Chapter 1 and 2 notebooks (and `probe_runs.csv` and `probe_summary.csv`) into its `stage-01/` and `stage-02/` folders. From then on, change `arpitRanjan` to your GitHub name in `REPO_URL` in each notebook's first cell, so Colab opens your copy.

## 2. One folder per stage

| Folder | What you put there |
| --- | --- |
| `stage-01/` | two notebook links: `01_first_calls` (10 calls, usage table with a forced truncation) and `01_probe_set` (10 probes x 5 runs x 2 models, predictions, README cell); keep `probe_runs.csv` and `probe_summary.csv` |
| `stage-02/` | both `02` notebooks, `labeled_random_30.csv`, `labeled_stratified_30.csv`, `failure_backlog.csv` (with your Stage 1 probe failures), README with the retention table |
| `stage-03/` | README, `CODEMAP.md`, `DEBUG.md`, `MCP.md`, `PRS.md`, `DEPLOYED.md`, `evals/` with the 50 run re-test (`scripts/retest.py`); prompts live in the root `prompts/` |
| `stage-04/` | your `04_baseline_vs_llm` run, `llm_results.csv`, `baseline_results.csv`, `comparison.md`, `stack_choice.md`, README strategy note |
| `stage-05/` | `PRD.md`, `evals/acceptance.jsonl`, `acceptance-run.txt` (`scripts/acceptance.py --url` against your deployed `app/api.py`), README, a named fallback in `app/app.py` |
| `stage-06/` | your runs of `06_harness` and `06_context_ablation`, `traces/run.jsonl`, `pass_rates.csv`, `failed_run.md`, `context_ablation.csv`, `compaction_check.csv` |
| `stage-07/` | `oversight_app.py` (approval, claim citations, refusal, feedback), `approvals.jsonl`, `feedback.jsonl`, the usability test in README |
| `stage-08/` | notes only; the eval build lives in `evals/`, `prompts/APPROVALS.md`, `notebooks/08_judge_calibration.ipynb`, `.github/workflows/evals.yml` |
| `stage-09/` | your runs of the three `09` notebooks, `rag_answers.jsonl`, `baseline_vs_retrieval.csv`, `retrieval_strategies.csv`, `retrieval_summary.json`, `stale_window.json` |
| `stage-10/` | your runs of the three `10` notebooks, `traces/spans.jsonl`, `tracing_summary.json`, `cost_lever.csv`, `metric-tree.md`, `ab_readout.md` |
| `stage-11/` | your run in `notebooks/`, `leak-test/`, `field-log.csv`, `audit-log.jsonl`, `change-evidence.csv`, `procurement-pack.md` |
| `stage-12/` | your run of `12_locale_eval`, `golden-set.jsonl`, `outputs.jsonl`, `judge-prompt.md`, `judge-agreement.md`, `results/ci-results.json` (run by `locale_evals.py` in CI) |
| `stage-13/` | your runs of the two `13` notebooks, `guardrail-summary.json`, `blocked_calls.jsonl`, `injection-runs.csv`, `redteam-outcomes.csv`, `fallback.json`, `authority-table.md` |
| `stage-14/` | README (from `templates/HANDOFF.md`), `SPEC.md`, `traces/`, `known-failures.md`, `peer-run-notes.md`, `evals-run.txt` (no notebook) |
| `stage-15/` | `TAKEHOME.md` (from `templates/`), README with the PR, live URL and recording links; root README from `templates/PORTFOLIO_README.md` (no notebook) |

Skipped a stage? Each `checkpoint/stage-NN` branch (01 to 15) has an example finished stage you can continue from:
`git checkout checkpoint/stage-01`. Those examples were made with the offline mock model.

## 3. Open the notebooks in Colab

These links open the kit's own copy. After you fork, replace `arpitRanjan` with your GitHub name to open yours:

- [01_first_calls](https://colab.research.google.com/github/arpitRanjan/atp-builder-kit/blob/main/notebooks/01_first_calls.ipynb)
- [01_probe_set](https://colab.research.google.com/github/arpitRanjan/atp-builder-kit/blob/main/notebooks/01_probe_set.ipynb)
- [02_sql_duckdb](https://colab.research.google.com/github/arpitRanjan/atp-builder-kit/blob/main/notebooks/02_sql_duckdb.ipynb)
- [02_traces_pandas](https://colab.research.google.com/github/arpitRanjan/atp-builder-kit/blob/main/notebooks/02_traces_pandas.ipynb)
- [04_baseline_vs_llm](https://colab.research.google.com/github/arpitRanjan/atp-builder-kit/blob/main/notebooks/04_baseline_vs_llm.ipynb)
- [06_agent_loop](https://colab.research.google.com/github/arpitRanjan/atp-builder-kit/blob/main/notebooks/06_agent_loop.ipynb)
- [06_harness](https://colab.research.google.com/github/arpitRanjan/atp-builder-kit/blob/main/notebooks/06_harness.ipynb)
- [06_context_ablation](https://colab.research.google.com/github/arpitRanjan/atp-builder-kit/blob/main/notebooks/06_context_ablation.ipynb)
- [06_structured_output](https://colab.research.google.com/github/arpitRanjan/atp-builder-kit/blob/main/notebooks/06_structured_output.ipynb)
- [08_judge_calibration](https://colab.research.google.com/github/arpitRanjan/atp-builder-kit/blob/main/notebooks/08_judge_calibration.ipynb)
- [09_rag_pipeline](https://colab.research.google.com/github/arpitRanjan/atp-builder-kit/blob/main/notebooks/09_rag_pipeline.ipynb)
- [09_retrieval_eval](https://colab.research.google.com/github/arpitRanjan/atp-builder-kit/blob/main/notebooks/09_retrieval_eval.ipynb)
- [09_permissions](https://colab.research.google.com/github/arpitRanjan/atp-builder-kit/blob/main/notebooks/09_permissions.ipynb)
- [10_tracing](https://colab.research.google.com/github/arpitRanjan/atp-builder-kit/blob/main/notebooks/10_tracing.ipynb)
- [10_cost_levers](https://colab.research.google.com/github/arpitRanjan/atp-builder-kit/blob/main/notebooks/10_cost_levers.ipynb)
- [10_ab_readout](https://colab.research.google.com/github/arpitRanjan/atp-builder-kit/blob/main/notebooks/10_ab_readout.ipynb)
- [11_customer_deployment](https://colab.research.google.com/github/arpitRanjan/atp-builder-kit/blob/main/notebooks/11_customer_deployment.ipynb)
- [12_locale_eval](https://colab.research.google.com/github/arpitRanjan/atp-builder-kit/blob/main/notebooks/12_locale_eval.ipynb)
- [13_guardrails](https://colab.research.google.com/github/arpitRanjan/atp-builder-kit/blob/main/notebooks/13_guardrails.ipynb)
- [13_injection_and_redteam](https://colab.research.google.com/github/arpitRanjan/atp-builder-kit/blob/main/notebooks/13_injection_and_redteam.ipynb)

The first cell clones the repo into Colab so the notebook can find `kit/` and `data/`, and installs only
what that notebook needs. Colab already has numpy, pydantic and sentence-transformers. The 09 notebooks
download two small Hugging Face models the first time they run live (about 90 MB each, a minute or two):
`all-MiniLM-L6-v2` for embeddings and `cross-encoder/ms-marco-MiniLM-L-6-v2` for reranking.

Locally (Python 3.11):

```
python3.11 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

`requirements.txt` includes PyTorch (for sentence-transformers). On Linux without a GPU, run
`pip install torch==2.15.0 --index-url https://download.pytorch.org/whl/cpu` first to skip about 3 GB.
promptfoo (Chapter 8) is an npm tool, not a pip package: it needs Node 20 or later and runs with `npx`.

## 4. How keys work

- **Colab:** click the key icon (Secrets) on the left, add `GEMINI_API_KEY`, turn on notebook access.
- **Locally:** copy `.env.example` to `.env` and fill it in. `.env` is in `.gitignore`. Never commit a key.
- **No Gemini key?** Fill in `FALLBACK_BASE_URL`, `FALLBACK_API_KEY` and `FALLBACK_MODEL` for any
  OpenAI style API (OpenAI, Groq, OpenRouter).
- **No key at all?** Set `KIT_OFFLINE=1`. Every call goes to a fake model with repeatable answers.
  For the Chapter 4 to 13 notebooks the fake model follows simple keyword rules (`kit/mock_brain.py`),
  and the embedder and reranker are deterministic stand-ins, so nothing is downloaded. Offline numbers
  only show the notebook works: run it live for numbers you can use.

`kit/llm.py` picks the provider in this order: `KIT_OFFLINE=1` (mock), `KIT_PROVIDER` if set,
Gemini if `GEMINI_API_KEY` exists, else the fallback. Edit prices in `kit/prices.py`.

## 5. The data rule

Free API tiers may use your prompts and answers to improve the provider's products. So use ONLY the
kit's synthetic data (everything in `data/` and the generated `corpus/`) or openly licensed data.
**Never put real customer data, real user messages or anything private into a prompt.**

## 6. Who can use the Gemini API

- You must be **18 or older** to use the Gemini API.
- **EEA, Switzerland and UK:** if your deployed app is public and serves users there, it must use a
  **paid** key. Otherwise keep the deployed app private (only you and invited testers).

## 7. What is inside

```
kit/llm.py            call_llm(): one function for Gemini, OpenAI style APIs and the mock
kit/prices.py         prices per million tokens, and cost()
data/make_data.py     makes the synthetic data (fixed seed); the CSV and JSONL files are committed
data/probes.csv       10 probe tasks with code-checkable pass criteria
notebooks/            one or more notebooks per chapter (see section 3)
scripts/call_model.py the same call with plain HTTP, to read raw JSON and tracebacks
corpus/make_corpus.py writes the Quillnote help pages (Quillnote is an invented app)
mcp_server/server.py  an MCP server with one read-only tool, search_docs
app/app.py            a small Streamlit help assistant, prompt from prompts/, named fallbacks
app/api.py            the same assistant as POST /ask, so scripts/acceptance.py can test your live URL
prompts/              versioned system prompts (help_v1.md ...) and APPROVALS.md
scripts/retest.py     the Stage 3 re-test: 10 inputs x 5 runs
kit/approval.py       approval payloads, approve/edit/reject log, claim citations, refusal and empty states
kit/feedback.py       thumbs-down and edit feedback as eval rows
stage-07/oversight_app.py  a Streamlit app with the approval screen and feedback (Stage 7)
kit/rag.py            parse, chunk, embed, index, BM25, fusion and rerank, for the 09 notebooks
kit/mock_brain.py     the offline mock's keyword rules for the Chapter 4 to 13 notebooks
kit/tracing.py        spans around the app's answer function (traces/spans.jsonl), percentiles, cost per task
kit/guardrails.py     input and output checks, refusal, rate limit, spend cap, host allowlist for tool handlers
scripts/acceptance.py acceptance cases (evals/acceptance.jsonl) against a ship bar: --bar 0.8 [--url URL] [--out FILE]
evals/                labels.csv (judge calibration), golden.jsonl (dev, held-out, regression), gates.py, promptfooconfig.yaml, run_evals.py
evals/retrieval_check.py  recall at k, citation faithfulness and the two user leak test (retrieval_questions.jsonl), for CI
stage-12/locale_evals.py  the Spanish golden set as a CI check
evals/ (wave 3)       golden_es.jsonl and labels_es.csv (Spanish), guardrail_probes.jsonl, regression.jsonl (red team)
data/customer_northwind/  a SIMULATED second customer (Northwind Learning, invented): brief, 10 pages, questions per role
templates/            HANDOFF.md, SPEC.md, KNOWN_FAILURES.md, PEER_RUN_NOTES.md (Stage 14), TAKEHOME.md and PORTFOLIO_README.md (Stage 15), PROCUREMENT_PACK.md (Stage 11)
Makefile              make evals (the eval suite in one command), make traces (20 traced requests, span export)
.github/workflows/evals.yml.example  rename to evals.yml to run the golden set on every pull request
tests/                pytest, all offline
```

### The agent tool protocol (06 notebooks)

The agent notebooks do not use a provider's native tool calling, because Gemini and OpenAI style APIs
format it differently. The system prompt asks the model to reply with ONE JSON object:
`{"tool": "search_docs", "args": {"query": "..."}}` to call a tool, or `{"final": "..."}` to finish.
The loop parses the outermost `{...}` from the reply, runs the tool in code, and adds `CALL n:` and
`RESULT n:` lines to the next prompt. The same loop runs on Gemini, any OpenAI style API and the mock.
`draft_issue` only appends to a local `outbox.jsonl` file; nothing is sent anywhere.

### Cached tokens and time to first token (Chapter 10)

`call_llm` also returns `cached_tokens` and `ttft_s`. Cached tokens come from
`usage.prompt_tokens_details.cached_tokens` (OpenAI) or `usage_metadata.cached_content_token_count`
(Gemini). `None` means the provider did not report it, which can happen on the Gemini free tier.
With `stream=True` the time to first token is measured on the stream; without it, it is the time to
the whole reply (`ttft_kind` says which). The offline mock makes both up.

### The handover bundle (Chapter 14)

```
make test      # offline tests
make evals     # the golden set through the app; exit 1 if a hard gate fails
make traces    # 20 traced requests, writes traces/spans.jsonl and traces/spans.csv (git ignores traces/)
```

Add `KIT_OFFLINE=1` in front of `make evals` or `make traces` to use the mock model.

### Evals in CI (Chapter 8)

```
python evals/run_evals.py                               # no npm: exit 1 if a hard gate fails
python evals/run_evals.py --bar 0.85                    # pass when 85% or more of cases pass the hard gates
npx promptfoo@0.125.1 eval -c evals/promptfooconfig.yaml # the same gates in promptfoo
```

Hard gates (must cite a right page, never cite an admin page, no empty or unsure answer) fail the run.
Advisory gates (length, number of pages cited) are reported and never fail it. To run it on every pull
request, rename `.github/workflows/evals.yml.example` to `evals.yml` and add your key as a repository secret.

## 8. Tests

```
KIT_OFFLINE=1 pytest -q
```

GitHub Actions runs this on every push, on pull requests and weekly (`.github/workflows/smoke.yml`).

## Tested with

- Python 3.11 on macOS, package versions as pinned in `requirements.txt`.
- All tests pass offline with the mock model.
- Live: notebook `01_first_calls` and the app logic through the `openai_compatible` provider with
  OpenAI `gpt-5.4-mini`.
- Live (2026-11-14): `06_agent_loop` and `09_rag_pipeline` through `openai_compatible` with `gpt-5.4-mini`,
  and `09_rag_pipeline` with the real local `all-MiniLM-L6-v2` embedder. The other new notebooks
  (04, 06 harness, context ablation and structured output, 08, 09 retrieval eval and permissions)
  were tested offline only.
- Live (2026-11-14, wave 3): `10_tracing` and `13_injection_and_redteam` through `openai_compatible`
  with `gpt-5.4-mini` (streaming time to first token, cached token field, the failover cell with
  `gpt-5.4-nano` as the second model, since only one provider key was used). The other wave 3
  notebooks (10 cost levers and A/B readout, 11, 12, 13 guardrails) were tested offline only.
  The Langfuse cell has not been sent to a real Langfuse account. Gemini streaming and Gemini's
  cached token field are untested.
- promptfoo 0.125.1 ran `evals/promptfooconfig.yaml` offline with Node 23 (same 17 of 20 hard gate
  passes as `evals/run_evals.py`). The `evals.yml.example` workflow has not run on GitHub yet.
- **Not tested live: Gemini.** The Gemini code in `kit/llm.py` and `scripts/call_model.py` follows the
  google-genai SDK and the generateContent REST API, but it has not been run against a real Gemini key.
  `scripts/call_model.py` was tested offline only.
- The `corpus/make_corpus.py` script has not been run yet.
