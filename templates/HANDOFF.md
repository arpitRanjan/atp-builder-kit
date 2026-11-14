# Handover: <your app name>

Fill in every `<...>`. The reader is an engineer or a forward deployed engineer who has never seen this
project. They should be able to run everything below cold, in under 30 minutes, without asking you.

## 1. What it does, in two sentences

<Who uses it, what they ask, what it answers from, and what it may do (tools).>

## 2. Run it cold

```
git clone <your fork URL> && cd atp-builder-kit
python3.11 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # then fill in a key, or skip it and use KIT_OFFLINE=1
make test                     # the offline tests, about a minute
make evals                    # the golden set in one command; exit 1 means a hard gate failed
make traces                   # 20 traced requests -> traces/spans.jsonl and traces/spans.csv
```

Expected results on <date>, with <provider and model>:

| Check | Result | Bar |
| --- | --- | --- |
| `make evals` hard gates | <17 of 20> | <18 of 20> |
| p95 latency (from `make traces`) | <ms> | <ms> |
| Cost per successful task | <$> | <$> |
| Red team pass^3 (`13_injection_and_redteam`) | <0.83> | <1.00> |

## 3. How it fits together

<One paragraph: question -> retrieval (with the role filter) -> model -> output check -> answer. Name the files.>

| Part | File | Notes |
| --- | --- | --- |
| Answer function | `app/app.py` | <what you changed> |
| Retrieval and roles | `kit/rag.py` | <chunk size, k, the access map> |
| Guardrails | `kit/guardrails.py` | <rate limit, spend cap, allowlist hosts> |
| Evals | `evals/` | golden set, regression cases, gates |
| Spans | `kit/tracing.py` | one JSON line per span |

## 4. Limits that are switched on

- Rate limit: <n> requests per user per <seconds>.
- Spend cap: <$ per day>, where it is set: <file or env var>.
- Tools that can act outside the app: <list>. Each one needs: <approval rule>.
- Host allowlist: <hosts>. It is checked in the tool handler, not at the network level.

## 5. Known issues and decisions

The field log is the source: `<path to field_log.csv>`. The three that matter most:

| Issue | Decision (configure, build, drop) | Why |
| --- | --- | --- |
| <...> | <...> | <...> |

## 6. What to watch in the first week

- <the span or metric that drives spend, and the alert level>
- <the eval case that fails first when the model changes>

## 7. Who to ask

<Name, role, how to reach them, and until when.>
