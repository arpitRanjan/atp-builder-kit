# app

A minimal Quillnote help assistant. It searches the help pages (the same code as the MCP tool), sends the
best snippets to the model, and shows the answer with the page ids it cites.

Two ways to serve the same `answer()` function:

- `app/app.py`: a Streamlit page. Deploy it on Streamlit Community Cloud (Stage 3).
- `app/api.py`: a small FastAPI app with a question page at `/` and `POST /ask`. Deploy it on Render or
  Hugging Face Spaces. `scripts/acceptance.py --url` needs this one, because Streamlit has no POST endpoint (Stage 5).

## Run locally

```
python corpus/make_corpus.py      # once, makes the help pages
streamlit run app/app.py
```

The endpoint (install `pip install -r app/requirements-api.txt` first):

```
uvicorn app.api:app --port 8000
curl -X POST localhost:8000/ask -H "Content-Type: application/json" -d '{"question": "How do I export a note as PDF?"}'
```

## Settings

At the top of `app/app.py`:

- `PROMPT_FILE`: the versioned system prompt in `prompts/` (`help_v1.md`, `help_v2.md` ...).
- `MAX_CALLS_PER_SESSION`: the Streamlit spend guard (the app stops after that many model calls in one browser session).
- `TOP_K`: how many pages it reads. `HIDE_VISIBILITY`: page visibilities it never reads, for example `["admin"]`.
- `FALLBACKS`: the message for each named failure. `no_page` fires when no help page matches
  (try the question `zzzz qqqq`). `model_error` fires when the model call fails. Each reply says which
  fallback fired in its `fallback` field. Add your own named fallback here for Stage 5.

At the top of `app/api.py` (or as environment variables on the host): `MAX_CALLS_PER_CLIENT` per client per
day (default 30) and `MAX_CALLS_PER_DAY` for the whole app (default 300). Over the limit, `/ask` replies 429
with `"fallback": "spend_guard"`. One acceptance run uses 15 or more calls, so keep the client limit above that.

## Deploy the Streamlit app to Streamlit Community Cloud

1. Push your fork to GitHub (the corpus files must be committed so the app can read them).
2. On share.streamlit.io, click **Create app**, pick your fork, branch `main`, file `app/app.py`.
3. Open **Advanced settings**, then **Secrets**, and paste:

   ```
   GEMINI_API_KEY = "your key"
   ```

   Never put the key in the code or in git. Locally, keep it in `.env`, which git ignores.
4. Deploy, then copy the URL into `stage-03/DEPLOYED.md`.

## Deploy the endpoint to Render (free web service)

1. On render.com, click **New**, then **Web Service**, and connect your fork.
2. Build command: `pip install -r app/requirements-api.txt`
3. Start command: `uvicorn app.api:app --host 0.0.0.0 --port $PORT`
4. Under **Environment**, add `GEMINI_API_KEY` (and `PYTHON_VERSION` = `3.11.9`).
5. Deploy. Open the URL to see the question page. Then run
   `python scripts/acceptance.py --bar 0.8 --url https://YOUR-APP.onrender.com --out stage-05/acceptance-run.txt`.
   A free Render service sleeps when idle, so the first request can take up to a minute. The script waits.

## Or deploy the endpoint to Hugging Face Spaces (free CPU)

1. Create a new Space, SDK **Docker**, blank template.
2. Copy `app/Dockerfile` to the root of the Space repo, then push the kit files to the Space
   (or copy them in with the web editor). The Space must contain `app/`, `kit/`, `mcp_server/`, `corpus/` and `prompts/`.
3. In the Space **Settings**, add a secret `GEMINI_API_KEY`.
4. The URL looks like `https://YOUR-NAME-YOUR-SPACE.hf.space`. Use it with `--url` as above.

## Set a spend cap at the provider

The in-app guards only limit sessions and days. Also set a budget or spend cap on the key itself in your
provider's console (Google AI Studio or Cloud billing, OpenAI usage limits), so a leaked key or a busy
day cannot run up a bill.

## EEA, Switzerland and UK rule

If the app is public and serves users in the EEA, Switzerland or the UK, the Gemini key must be a
**paid** key. Otherwise keep the app private: in Streamlit Cloud app settings, set sharing to
"Only specific people can view this app". A Hugging Face Space can be set to private. A Render web
service is public to anyone with the URL, so use a paid key there if those users can reach it.
Say which choice you made in `stage-03/DEPLOYED.md`.
