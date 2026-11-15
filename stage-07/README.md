# Stage 7: approval UX, safer responses and feedback logging

## Live app

<your live URL> (Streamlit Community Cloud, app file `stage-07/oversight_app.py`).

## Approval screen

Where it lives: ask the assistant to "Draft an issue titled ...". Before anything is written, the app shows
a review table and three buttons: Approve, Edit and Reject (`approval_screen()` in `oversight_app.py`).

Fields the user can verify before confirming: title, body, related pages (id and title), the visibility of
those pages, the destination (a local outbox file, nothing is sent), who asked, and the run id. A warning
shows when a related page is admin only. Edit opens the title and body for changes; the log keeps the diff.

Evidence: `approvals.jsonl`, 7 rows: 3 approve, 2 edit, 2 reject. Each row has a timestamp, the session
and run ids, the outcome, the payload reviewed and the payload diff for edits.

## Claim-level citations

Each sentence of an answer is a claim, shown with its own source page (`cite_claims()` in `kit/approval.py`).
A claim with no supporting page shows "no source: check this" instead of hiding it.

- "How do I export a note as PDF?": every step claim shows `[qn-02] Export a note as PDF`.
- "I deleted a note by accident. Can I get it back?": the Trash steps show `[qn-07] Recover a deleted note`;
  the last generic sentence shows "no source", which is the mock model padding the answer.

## Refusal and empty state

Real refusal, for "Give me the admin console steps to refund a double charge":

> I cannot do admin actions or show admin only steps.
> Why: Refunds, user deletion, billing changes and the audit log are for workspace admins only.
> What you can do: Ask your workspace admin, or ask me how to find who your admin is.

The 3 suggested prompts in the empty state:

1. How do I export a note as PDF?
2. I deleted a note by accident. Can I get it back?
3. PDF export cuts off wide tables. Draft an issue titled "PDF export cuts off tables".

Feedback: `feedback.jsonl` has 3 rows (2 thumbs down, 1 edit), each with the signal, prompt, answer id,
answer, and the edited text or reason.

## Usability test

Task: ask for a bug report draft, check it, then approve, edit or reject it.
Seeded mistake: the draft links the wrong help page (Plans and pricing instead of the page the bug is about).

| Participant | Caught the seeded mistake? | Seconds to verify | Edited before confirming? | Outcome |
| --- | --- | --- | --- | --- |
| <P1> | <yes or no> | <seconds> | <yes or no> | <outcome> |
| <P2> | | | | |
| <P3> | | | | |

- Catch rate: <n>/3
- Average time to verify: <seconds>
- Edit rate before confirming: <n>/3

## What I measured

7 approval decisions over 4 drafts, and 3 feedback rows. 2 of the 7 payloads linked an admin only page
(qn-15, Read the audit log) to a PDF export bug, and the review table showed the admin warning both times.
The 2 seeded mistakes were caught: one edited, one rejected.

## What went wrong

Both payloads with the admin page went through: one approved as it was, one edited (title only) with the
admin page still in it. The warning alone did not stop it.

## What I would do next

Block admin pages from the related pages in code, before the approval screen, and re-run the usability test.
