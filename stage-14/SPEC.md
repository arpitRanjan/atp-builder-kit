# Spec: Quillnote help answer (example)

## What it does

Quillnote users ask how to do something in the app. The assistant answers only from the 15 help pages and cites them.

## Production boundary

### In scope

- How-to answers from the public and team help pages, with cited page ids.
- A refusal that points to public pages and to support when a question is blocked.
- A draft bug report to the local outbox, when the user asks for one.

### Out of scope

- Admin procedures (refunds, data deletion): admin pages are never shown to public or team users.
- Answers not in the help pages, account changes, billing changes, sending any message.
- Spanish answers (on hold after stage 12).

### Where human approval is required

| Drafted action | Who approves | How (file or rule) |
| --- | --- | --- |
| `draft_issue` to the docs team | a person on the docs team, before anything is sent | approval in code: the user's task asks for an issue and the address is on `@quillnote.example` (`require_approval` in `notebooks/13_injection_and_redteam.ipynb`) |
| `fetch_url` | nobody: only `help.quillnote.example` is allowed | `HostAllowlist.guard` in `kit/guardrails.py`, inside the handler |

Nothing drafted is taken before that approval.

## Ship bar

Hard gates on the golden set (`evals/golden.jsonl`): 18 of 20 or better. Current: 20 of 20 (offline mock).

## Fallback

When the main model fails, the backup model answers with a "Backup mode" note (stage 13, `stage-13/fallback.json`).
