# app

A minimal Quillnote help assistant. It searches the help pages (the same code as the MCP tool), sends the
best snippets to the model, and shows the answer with the page ids it cites.

## Run locally

```
python corpus/make_corpus.py      # once, makes the help pages
streamlit run app/app.py
```

Settings are at the top of `app/app.py`: `MAX_CALLS_PER_SESSION` is the spend guard (the app stops after
that many model calls in one browser session), `TOP_K` is how many pages it reads.

## Deploy to Streamlit Community Cloud

1. Push your fork to GitHub (the corpus files must be committed so the app can read them).
2. On share.streamlit.io, click **Create app**, pick your fork, branch `main`, file `app/app.py`.
3. Open **Advanced settings**, then **Secrets**, and paste:

   ```
   GEMINI_API_KEY = "your key"
   ```

   Never put the key in the code or in git.
4. Deploy, then copy the URL into `stage-03/DEPLOYED.md`.

## Set a spend cap at the provider

The in-app guard only limits one session. Also set a budget or spend cap on the key itself in your
provider's console (Google AI Studio or Cloud billing, OpenAI usage limits), so a leaked key or a busy
day cannot run up a bill.

## EEA, Switzerland and UK rule

If the app is public and serves users in the EEA, Switzerland or the UK, the Gemini key must be a
**paid** key. Otherwise keep the app private: in Streamlit Cloud app settings, set sharing to
"Only specific people can view this app".
