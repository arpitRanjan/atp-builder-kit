# AI assisted change and a real debug step: scripts/call_model.py

- The change I asked an AI coding tool to make: time each call and save a `latency_s` column in `runs.csv`.
- Commit with the change: `<commit link>`

## The failed run

I ran the changed script in a new terminal, without the key loaded:

```
Traceback (most recent call last):
  File "scripts/call_model.py", line 35, in <module>
    data = call_once()
           ^^^^^^^^^^^
  File "scripts/call_model.py", line 28, in call_once
    key = os.environ["GEMINI_API_KEY"]
          ~~~~~~~~~~^^^^^^^^^^^^^^^^^^
  File "<frozen os>", line 679, in __getitem__
KeyError: 'GEMINI_API_KEY'
```

## What caused it and the fix

The last line says the environment had no `GEMINI_API_KEY`: the script only read the environment, and my key
was in the untracked `.env` file. The fix reads the key with `kit.llm.get_secret`, which checks the environment
and `.env`, and stops with a clear message when the key is missing.

- Commit with the fix: `<commit link>`
