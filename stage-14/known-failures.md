# Known failures (example)

Traces are in [traces/spans.jsonl](traces/spans.jsonl). Find a trace by its `trace_id`.

| # | Failure or sharp edge | User impact | Trace |
| --- | --- | --- | --- |
| 1 | Spanish question "¿Cómo creo una nota nueva...?" (es01) cites the admin page qn-14 | a normal user is shown an admin procedure about deleting user data | `traces/spans.jsonl`, trace_id `8956d7f10900` |
| 2 | Spanish question "Borré una nota por error..." (es09) cites the wrong page | the user does not learn that Trash can restore the note | `traces/spans.jsonl`, trace_id `bb4c65b5c033` |
| 3 | Mixed language "how do I recuperar una nota que borré?" (es18) cites the wrong page | users who mix languages get a wrong answer | `traces/spans.jsonl`, trace_id `034522d70e75` |
| 4 | `app/app.py` has no per user role filter (`HIDE_VISIBILITY` is empty by default), so failure 1 can happen in English too when a question shares words with an admin page | an admin page could reach a public user; the output check in `kit/guardrails.py` is the only stop | `traces/spans.jsonl`, trace_id `8956d7f10900` (the retrieval span lists qn-14) |
