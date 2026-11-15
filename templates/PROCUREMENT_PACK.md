# Procurement pack: <your assistant> for <customer>

Copy this to `stage-11/procurement-pack.md`. Every answer links to an exact file in your repo. Fill in every `<...>`.

## 1. Can one role see another role's pages? (leak test)

<Answer in one or two sentences, with the counts.> Evidence: [leak test summary](leak-test/summary.md),
raw results in [leak-test/](leak-test/), the role filter in <file and function>.

## 2. What do you keep, for how long, and what is redacted? (retention and redaction)

| Data | Where it is kept | How long | Redaction |
| --- | --- | --- | --- |
| Audit log | [audit-log.jsonl](audit-log.jsonl) | <days> | no raw question or answer text, only ids and counts |
| Answers | [answers.jsonl](answers.jsonl) | <days> | <practice data only; real user text is not stored> |
| Provider side | <provider> | <their retention> | <what you send them> |

## 3. Can we see what the agent did? (audit log of agent actions)

<What one line holds, and how a buyer reads it.> Evidence: [audit-log.jsonl](audit-log.jsonl), written by <file>.

## 4. What does the model provider do with our data? (provider data terms)

Provider and model used: <from the notebook's step 2 output>. Their terms: <link to the provider's data use
page>. Free tier note: <free tiers may use prompts to improve the provider's products; that is why only
synthetic data is used>. What a paid plan changes: <one line>.

## 5. Do users know they are talking to an AI? (AI disclosure)

The text users see: "<the DISCLOSURE text from the notebook, or your app's text>". Where it is shown:
<file and line, or a screenshot path>.

## Open items

- <anything the buyer asked that you cannot answer yet, and when you will>
