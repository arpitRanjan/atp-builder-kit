# Stage 12: Spanish readiness pack (example)

Example made with the offline mock model. See `EXAMPLE.md`.

## The variant

- Feature: the help answer (question in, answer with cited help pages out).
- Target language: Spanish.
- Why: the kit ships Spanish practice cases and Spanish hand labels, and the app's keyword search only matches English words, so it is the clearest gap.
- What stayed the same from Stage 8: the hard gates in `evals/gates.py` (cite the right page, never cite admin pages), the judge prompt wording, and the CI workflow. The kit's workflow already has the Spanish step, so I did not need to add one.
- The variant code: `localized_ask` in [locale_evals.py](locale_evals.py): translate the question into English for search only, then answer in the user's language.

## Files

- Golden set: [golden-set.jsonl](golden-set.jsonl), 20 cases (15 translated, 5 degraded: 2 typo, 1 no accents with a typo, 2 mixed Spanish and English). Each has `input`, `expected` and `source` (the kit question it was translated from).
- Real outputs: [outputs.jsonl](outputs.jsonl), pass rates: [results.csv](results.csv).
- CI: [../.github/workflows/evals.yml](../.github/workflows/evals.yml) already has the Spanish step (you do not need to add it). Once `golden-set.jsonl` is committed it runs `python stage-12/locale_evals.py --bar 0.8`, which writes [results/ci-results.json](results/ci-results.json) and exits 1 under 80 percent.
- Judge: [judge-prompt.md](judge-prompt.md), agreement in [judge-agreement.md](judge-agreement.md).

## Results

- Main metric, hard gate pass rate: app as is 3 of 15 translated (20 percent) and 2 of 5 degraded (40 percent); with the variant 20 of 20 (100 percent). English stays at 15 of 15.
- Judge agreement on 10 Spanish hand labels: 7 of 10 (70 percent). All 3 disagreements are bad answers the judge passed: one wrong detail (e04), a wrong permission (e08), an opposite fact (e10).
- Main failure pattern: with the app as is, Spanish questions find the wrong pages or none, because search matches English words. The judge misses answers that reuse the right words with one wrong fact.
- Next: run live, check that answers come back in Spanish, and fix the judge (ask it to list each fact and check it against the reference) before trusting it in Spanish.

Readiness call (ship, hold, or ship with a named limit): **hold**
