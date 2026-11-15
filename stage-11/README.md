# Stage 11: Northwind Learning deployment (example)

Example made with the offline mock model. See `EXAMPLE.md`.

## Decisions, Measures, and Next

**Customer setup.** Northwind Learning, a simulated tutoring firm (`data/customer_northwind/`): 10 help pages,
12 questions, three roles (student, tutor, admin). Model provider: `mock` (`mock-model`), from step 2 of
[the notebook](notebooks/11_customer_deployment.ipynb). This builds on the Stage 10 readout in [../stage-10/README.md](../stage-10/README.md).

**Decisions.**
- Retrieval points at their pages, with their own access map (student pages for everyone, tutor pages for tutors and admins, admin pages for admins only).
- Retrieval k = 3 for answers, k = 5 for the leak test, so the leak test is stricter than the app.
- The prompt does not mention support. The support line is added in code (`SUPPORT_LINE` in `answer.py`), so it cannot be skipped by the model.
- Dropped for the pilot: a parent role (parents use the student login).

**Measures (from the run).**
- Answered from the right page: 10 of 12 questions ([answers.jsonl](answers.jsonl)).
- Leak test: student 16 of 16 passed, tutor 16 of 16, admin 16 of 16; the control with the filter off leaked on 16 of 16, so the test can fail ([leak-test/summary.md](leak-test/summary.md)).
- Field log: 10 rows, 5 configure, 4 build, 1 drop ([field-log.csv](field-log.csv)). Recurring items: "access map written by hand" (3 rows), "no contact support line" (3 rows), "question not answered from the right page" (2 rows).

**The change I shipped.** Recurring item: "no contact support line" (3 rows, one per role). Change: when no page is
cited, the answer ends with a support line. Changed file: `stage-11/answer.py` (`SUPPORT_LINE` and `answer_with_support()`), commit
`<commit hash>`. Before and after ([change-evidence.csv](change-evidence.csv)): out of scope answers with a support
line went from 0 of 3 to 2 of 3. The third (tutor) answer cited a wrong page instead of saying it did not know, so the rule never fired.

**Procurement.** The buyer's questions, each answered with a link to a file in this repo, are in
[procurement-pack.md](procurement-pack.md).

**Next.** Make the access map a per customer setting instead of code (the other recurring item), and catch
confident wrong citations on out of scope questions, which the support line cannot fix.
