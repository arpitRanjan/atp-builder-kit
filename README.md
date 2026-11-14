# AllthingsPM builder kit

A starter repo for the AllthingsPM AI product management course. You fork it once and build ONE project
in it, stage by stage. The lessons do the teaching; this kit gives you working code, synthetic data and
tests so you can spend your time on product decisions, not setup.

## 1. When to fork

Chapters 1 and 2 need no GitHub account: open the notebooks straight from the links in section 3, run them in Colab, and save your copy to your Google Drive (File, then Save a copy in Drive).

In Chapter 3 you fork the kit: click **Fork** on GitHub, and your copy lives at `https://github.com/<you>/atp-builder-kit`. Move your Chapter 1 and 2 notebooks into its `stage-01/` and `stage-02/` folders. From then on, change `arpitRanjan` to your GitHub name in `REPO_URL` in each notebook's first cell, so Colab opens your copy.

## 2. One folder per stage

| Folder | What you put there |
| --- | --- |
| `stage-01/` | your runs of the two `01` notebooks, plus `predictions.md` |
| `stage-02/` | your runs of the two `02` notebooks, plus `failure_backlog.csv` |
| `stage-03/` | `CODEMAP.md`, `prompts/`, your MCP tool, `DEPLOYED.md` |

Skipped a stage? Each `checkpoint/stage-NN` branch has an example finished stage you can continue from:
`git checkout checkpoint/stage-01`. Those examples were made with the offline mock model.

## 3. Open the notebooks in Colab

These links open the kit's own copy. After you fork, replace `arpitRanjan` with your GitHub name to open yours:

- [01_first_calls](https://colab.research.google.com/github/arpitRanjan/atp-builder-kit/blob/main/notebooks/01_first_calls.ipynb)
- [01_probe_set](https://colab.research.google.com/github/arpitRanjan/atp-builder-kit/blob/main/notebooks/01_probe_set.ipynb)
- [02_sql_duckdb](https://colab.research.google.com/github/arpitRanjan/atp-builder-kit/blob/main/notebooks/02_sql_duckdb.ipynb)
- [02_traces_pandas](https://colab.research.google.com/github/arpitRanjan/atp-builder-kit/blob/main/notebooks/02_traces_pandas.ipynb)

The first cell clones the repo into Colab so the notebook can find `kit/` and `data/`.

Locally (Python 3.11):

```
python3.11 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

## 4. How keys work

- **Colab:** click the key icon (Secrets) on the left, add `GEMINI_API_KEY`, turn on notebook access.
- **Locally:** copy `.env.example` to `.env` and fill it in. `.env` is in `.gitignore`. Never commit a key.
- **No Gemini key?** Fill in `FALLBACK_BASE_URL`, `FALLBACK_API_KEY` and `FALLBACK_MODEL` for any
  OpenAI style API (OpenAI, Groq, OpenRouter).
- **No key at all?** Set `KIT_OFFLINE=1`. Every call goes to a fake model with repeatable answers.

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
notebooks/            the four stage 1 and stage 2 notebooks
scripts/call_model.py the same call with plain HTTP, to read raw JSON and tracebacks
corpus/make_corpus.py writes the Quillnote help pages (Quillnote is an invented app)
mcp_server/server.py  an MCP server with one read-only tool, search_docs
app/app.py            a small Streamlit help assistant
tests/                pytest, all offline
```

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
- **Not tested live: Gemini.** The Gemini code in `kit/llm.py` and `scripts/call_model.py` follows the
  google-genai SDK and the generateContent REST API, but it has not been run against a real Gemini key.
  `scripts/call_model.py` was tested offline only.
- The `corpus/make_corpus.py` script has not been run yet.
