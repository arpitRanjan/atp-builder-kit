# Stage 13: trust, safety, and agent security for your help assistant

Run `notebooks/13_guardrails.ipynb` and `notebooks/13_injection_and_redteam.ipynb`. They write every file below into `stage-13/`.

## Checklist: files the grader looks for

| File | What it is | Made by |
| --- | --- | --- |
| `stage-13/13_guardrails.ipynb` | your run, saved with outputs | you: run `notebooks/13_guardrails.ipynb`, save a copy here |
| `stage-13/13_injection_and_redteam.ipynb` | your run, saved with outputs | you: run `notebooks/13_injection_and_redteam.ipynb`, save a copy here |
| `stage-13/guardrail-runs.csv` | every probe: refused or not, generation latency, check latency, added latency | guardrails step 4 |
| `stage-13/guardrail-summary.json` | false refusal rate, added latency, output check, rate limit and spend cap evidence | guardrails steps 4 to 7 |
| `stage-13/blocked_calls.jsonl` | the logged call the host allowlist blocked inside the `fetch_url` handler | injection step 7 |
| `stage-13/injected-docs/qn-02.md` | the COPY of one help page with the planted injection (`corpus/` is never changed) | injection step 4 |
| `stage-13/injection-runs.csv` | 5 runs with no defense and 5 with approval in code: did the injected action fire | injection steps 5 and 6 |
| `stage-13/outbox.jsonl` | the drafts the agent wrote (a local file, nothing is sent) | injection steps 5 to 9 |
| `stage-13/redteam_runs.csv` and `redteam-outcomes.csv` | six attacks, 3 runs each, with no defense and defended; the worst failure | injection step 9 |
| `stage-13/redteam-summary.json` | pass^3, the worst attack, injection counts | injection steps 9 and 10 |
| `evals/regression.jsonl` | all six attacks, rerun from the file every time | injection step 8 (add your own attacks here) |
| `stage-13/fallback.json` | main and fallback model pass rates, the gap, the routing rule, the degraded mode message | injection step 10 |
| `stage-13/authority-table.md` | one row per tool: authority, reversibility, who approves, worst likely mistake | the kit ships a starter (search_docs, fetch_url, draft_issue); injection step 11 keeps it. Edit it |
| `stage-13/README.md` | your README (replace this checklist) | you |

## Put the guardrails in your app

The notebooks prove the checks work. The brief wants them in the app too. In your answer path (for example `app/app.py`), call `guarded_answer` from `kit/guardrails.py`:

```
from kit.guardrails import RateLimiter, SpendCap, guarded_answer, input_rules, model_input_check

LIMITER, CAP = RateLimiter(5, 60), SpendCap(5.0)  # 5 questions per user a minute, $5 a day

def check(q):
    ok, reason = input_rules(q)
    return (ok, reason, None) if not ok else model_input_check(q)

def generate(q):
    return answer(q)  # returns text, cited and call

result = guarded_answer(question, user_id, generate, check, role=role, visibility=visibility, limiter=LIMITER, cap=CAP)
```

That gives the input check in parallel with generation, the output check, the refusal with a fallback response, the per-user rate limit and the spend cap. The host allowlist is `HostAllowlist(...).guard(fetch_url)`: it runs inside the tool handler. The app already has one:
`app/tools.py` wraps `fetch_url` this way and logs blocked calls to `stage-13/blocked_calls.jsonl`. Point your
README at it, and add your own hosts to `ALLOWED_HOSTS` there.

## Your README must have

A section called **Decisions and results** that says: what you shipped, what you measured, the false refusal
rate, the added latency, pass^3 (k = 3), the fallback model pass rate gap, the routing rule, the degraded mode
users see, the worst red team issue you fixed (from `redteam-outcomes.csv`) and how, and what you would do next.
Link the authority table and the blocked call log.

## Submit

The GitHub folder link to `stage-13/`.

Offline (`KIT_OFFLINE=1`) the mock obeys any instruction it reads, so it shows the worst case, and its latencies are made up. Run live for the numbers in your README.
