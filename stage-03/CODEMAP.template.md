# Code map

Find each line with `grep -n`, for example `grep -n "call_llm(" app/app.py`. Use a range when it spans lines.

| What | File and line |
| --- | --- |
| App entry point | `app/app.py` line <n> (`main()`), or `app/api.py` line <n> |
| Model call | `app/app.py` line <n> (`call_llm(...)` in `answer()`) |
| Prompt file load | `app/app.py` lines <n to n> (`PROMPT_FILE`, `SYSTEM`), prompt text in `prompts/help_v<N>.md` |
| Main config values | `app/app.py` lines <n to n> (`MAX_CALLS_PER_SESSION`, `TOP_K`, `HIDE_VISIBILITY`) |
| API key or environment variable load | `app/app.py` line <n> (`load_keys`) and `kit/llm.py` line <n> (`get_secret`) |
