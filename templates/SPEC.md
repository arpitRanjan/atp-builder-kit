# Spec: <feature name>

Copy this file to `stage-14/SPEC.md`. Start from your `stage-05/PRD.md` and bring it up to date with what is in the repo today.

## What it does

<Two or three sentences: the user, the job, what it answers from.>

## Production boundary

### In scope

- <what the assistant does today, for example: answers how-to questions from the help pages, with cited page ids>

### Out of scope

- <what it does not do, for example: billing changes, account deletion, answers not in the help pages>

### Where human approval is required

| Drafted action | Who approves | How (file or rule) |
| --- | --- | --- |
| <draft_issue to the docs team> | <a person on the docs team> | <approval rule in code, file and function> |

Nothing drafted is taken before that approval.

## Ship bar

<Metric, threshold, dataset (from stage 5 and stage 8). Current result.>

## Fallback

<What users see when the model fails or the backup model serves (stage 13).>
