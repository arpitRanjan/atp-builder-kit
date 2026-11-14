# Take-home brief: <title>

Fill in every `<...>` before you send it. Keep it to one page: a long brief tests reading, not judgment.

## Context

<Two or three sentences: the product, the user, and the problem. Say plainly that all data is synthetic.>

## The task

<One task with a clear finish line, for example: "Our help assistant cites the wrong page for about one
question in five. Find out why, fix the biggest cause, and show the before and after.">

## What you get

- This repo, with the kit's synthetic data and help pages. No real customer data.
- `make test`, `make evals` and `make traces` already work. Run them first.
- <Any extra file, and what it is.>

## What to send back

1. A short write-up (one page): what you found, what you changed, what you would do next.
2. The numbers before and after, from `make evals` and `make traces`.
3. Your code as a branch or a pull request. No keys in it: search the branch for your key before you send it.

## Time box

<3 to 4> hours. Stop when the time is up and write down what you would do with more.

## How we will judge it

| What | What good looks like |
| --- | --- |
| Diagnosis | names the cause with evidence (a trace, a failing case), not a guess |
| Fix | the smallest change that moves the number, with a test that would catch it again |
| Measurement | before and after on the same cases, with the run to run spread noted |
| Judgment | says what was not fixed and why, and what it would cost |

## Rules

- Use any tools, including AI assistants. Say which ones you used and for what.
- Synthetic data only. Never paste real customer data or real user messages into a prompt.
- Questions: <email>. We reply within <one working day>.
