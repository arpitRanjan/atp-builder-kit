# Code map

| What | File and line |
| --- | --- |
| App entry point | `app/app.py` lines 74 to 98 (`main()`, run by `streamlit run app/app.py`); HTTP version `app/api.py` line 31 (`app = FastAPI(...)`) |
| Model call | `app/app.py` line 52 (`call_llm(build_prompt(question, hits), system=SYSTEM, ...)` in `answer()`) |
| Prompt file load | `app/app.py` lines 22 to 23 (`PROMPT_FILE`, `SYSTEM`); prompt text in `prompts/help_v2.md` |
| Main config values | `app/app.py` lines 19 to 22 (`MAX_CALLS_PER_SESSION`, `TOP_K`, `HIDE_VISIBILITY`, `PROMPT_FILE`) |
| API key or environment variable load | `app/app.py` lines 64 to 69 (`load_keys`, Streamlit secrets to env) and `kit/llm.py` lines 36 to 48 (`_load_dotenv`, `get_secret`) |
