# Stage 7: approval UX, safer responses and feedback logging

Submit: the live app URL, plus the GitHub link to your repo's `stage-07/` folder.

The kit gives you a working start: `stage-07/oversight_app.py` is the help assistant with every Stage 7 screen.
It uses the same `answer()` as `app/app.py`, and the helpers in `kit/approval.py` and `kit/feedback.py`.

```
streamlit run stage-07/oversight_app.py
```

Deploy it like the Stage 3 app (Streamlit Community Cloud, app file `stage-07/oversight_app.py`, same secrets),
or move its screens into `app/app.py`. Either way, put the live URL at the top of your README.

## What the app has (check each one in YOUR live app)

| Brief item | Where it is | Code |
| --- | --- | --- |
| Approval screen for the Stage 6 draft action, with Approve, Edit and Reject over the fully resolved payload | Ask "... Draft an issue titled ..."; the review table shows title, body, related pages, page visibility, destination, requester and run id | `approval_screen()`, `kit/approval.py` `resolve_payload()` |
| Claim-level citations | Each sentence of an answer shows its own source page (or "no source: check this") | `kit/approval.py` `cite_claims()` |
| Structured refusal state | Limit, reason and a next step, for admin actions, other people's data, prompt leaks and off-topic asks | `kit/approval.py` `check_request()` |
| Empty state with 3 suggested prompts | Shown before the first question | `kit/approval.py` `SUGGESTED_PROMPTS` |
| Thumbs-down and edit feedback that writes an eval row | "Was this wrong?" under each answer | `kit/feedback.py` `log_feedback()` |
| Seeded mistake for the usability test | Sidebar: "Usability test: plant one mistake in the next draft" | `kit/approval.py` `seed_mistake()` |

## Checklist: files in stage-07/

| File | What it must show | Made by |
| --- | --- | --- |
| `oversight_app.py` (or your changes to `app/app.py`) | The code for the screens above | you, starting from the kit |
| `approvals.jsonl` | At least 6 real rows across approve, edit and reject. Each row: `timestamp`, `session_id`, `run_id`, `outcome`, `payload`, `payload_diff` | the app, as you test it |
| `feedback.jsonl` | At least 3 real rows. Each row: `signal`, `prompt`, `answer_id`, `answer`, `edited_text`, `reason` | the app, as you test it |
| `outbox.jsonl` | The drafts that were approved. Local only, nothing is sent | the app |
| `README.md` | The sections below | you |

A deployed app cannot write into your GitHub repo. Use the download buttons in the app's sidebar, then
commit the files here. Or run the app locally, where it writes straight into `stage-07/`.
Never log real user data: test with the kit's synthetic help pages only.

## README.md sections (use these headings)

- `## Live app` (the URL)
- `## Approval screen` (where it lives, and the fields a user can verify before confirming)
- `## Claim-level citations` (2 example prompts from real runs, and how the citation shows for each claim)
- `## Refusal and empty state` (one real refusal example, and the 3 suggested prompts you shipped)
- `## Usability test` (the task, the seeded mistake, the results table, catch rate, average time to verify, edit rate)
- `## What I measured`, `## What went wrong`, `## What I would do next`

## Usability test (3 people, same task, one seeded mistake)

Task: "Ask the assistant to draft an issue for a bug, check the draft, then approve, edit or reject it."
Turn on the seeded mistake in the sidebar before each session: the draft then links the wrong help page.
`approvals.jsonl` records `seconds_to_decide` and `seeded_mistake` for every decision. Copy this table:

| Participant | Caught the seeded mistake? | Seconds to verify | Edited before confirming? | Outcome |
| --- | --- | --- | --- | --- |
| P1 | yes / no | | yes / no | approve / edit / reject |
| P2 | | | | |
| P3 | | | | |

- Catch rate = people who caught the mistake / 3
- Average time to verify = mean of "Seconds to verify"
- Edit rate = people who edited before confirming / 3
