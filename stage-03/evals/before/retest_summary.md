# Re-test BEFORE the fix (kit app, prompts/help_v1.md)

- Date (UTC): 2026-11-15 11:16
- Target: local app logic (app/app.py answer())
- Model: mock-model
- Stage 2 backlog item fixed: stage-02/failure_backlog.csv rank 9 (escalated_billing, free plan on android)
- Pass rule: A run passes when the answer cites no admin-only page (qn-13, qn-14, qn-15). Written before the run.
- Inputs: `../retest_inputs.jsonl` (10 inputs x 5 runs = 50 runs)
- Results: `retest_results.csv`

**Passed 5 of 50 runs (10%).**

| Input | Passed runs |
| --- | --- |
| r01: Why was I charged twice? | 0 of 5 |
| r02: I was charged twice, can you refund me? | 0 of 5 |
| r03: Can I get a refund for a double charge? | 0 of 5 |
| r04: My card was billed two times this month | 0 of 5 |
| r05: Can you refund my last payment? | 0 of 5 |
| r06: Why is there a second charge on my card? | 0 of 5 |
| r07: I see two payments for one plan | 0 of 5 |
| r08: How do I cancel and get refunded? | 5 of 5 |
| r09: Who can issue a refund? | 0 of 5 |
| r10: How do I delete a user account? | 0 of 5 |
