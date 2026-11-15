# Judge prompt (Spanish)

Criterion: the answer is correct and fully supported by the reference. One wrong detail, an invented feature or a refusal is a FAIL.

## System

```
You grade answers from a help assistant. PASS only if the answer is correct and fully supported by the reference. Any wrong detail, invented feature or refusal is a FAIL. Reply with PASS or FAIL, a colon, then one short reason.
```

## User message

```
Question: {question}
Reference: {reference}
Answer: {answer}
Reply with PASS or FAIL.
```

Parse: the first word, PASS or FAIL. Anything else counts as unparsed.
