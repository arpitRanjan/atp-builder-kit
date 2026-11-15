# PRD: <feature name>

## Context

<2 or 3 sentences. Use your Stage 4 strategy note and baseline numbers, with links:
../stage-04/README.md, ../stage-04/comparison.md>

## Production boundary for this version

<plain words: who it is for, what it does, what it will not do in this version>

## Failure modes

| Failure mode | What the user sees | Recovery or fallback |
| --- | --- | --- |
| <name 1> | <symptom> | <fallback path> |
| <name 2> | <symptom> | <fallback path> |
| <name 3> | <symptom> | <fallback path> |
| <name 4> | <symptom> | <fallback path> |

The fallback built in the app for this version: <name>.

## Guardrails

| Always | Ask first | Never |
| --- | --- | --- |
| <action> | <action> | <action> |

My feature's action, <action>, is in <bucket> because <reason>.

## Ship bar (set before any eval run)

- Metric: <for example acceptance pass rate>
- Threshold: <a number, for example 0.90>
- Dataset: `stage-05/evals/acceptance.jsonl` (<n> cases: normal <n>, edge <n>, failure <n>)

## Acceptance criteria

<one line per criterion; each maps to cases in evals/acceptance.jsonl>

## Model

- Model or setting tested: <model, temperature, output cap, prompt version>
- If it changes, re-test: <what you would run again>

## After launch

- Metric to watch: <one metric and where you would read it>
