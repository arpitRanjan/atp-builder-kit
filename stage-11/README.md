# Stage 11: ship your assistant into somebody else's company

You stand the assistant up for Northwind Learning, a simulated customer in `data/customer_northwind/`.
Run `notebooks/11_customer_deployment.ipynb`. It writes every file below into `stage-11/`.

## Checklist: files the grader looks for

| File | What it is | Made by |
| --- | --- | --- |
| `stage-11/notebooks/11_customer_deployment.ipynb` | your run, saved with outputs. It names the model provider. | you: run `notebooks/11_customer_deployment.ipynb`, save a copy to this path |
| `stage-11/answers.jsonl` | every Northwind question, the role, pages retrieved and cited, the answer | notebook step 4 |
| `stage-11/audit-log.jsonl` | one line per agent action: time, role, question id, pages, provider, model, tokens. No raw text. | notebook step 4 |
| `stage-11/leak-test/summary.md` | the leak test table: every role, prompts run, passed, failed, link to raw output | notebook step 5 |
| `stage-11/leak-test/raw-<role>.jsonl` | the raw leak test results per role, plus a control run with the filter off | notebook step 5 |
| `stage-11/field-log.csv` | every configuration choice, issue and workaround. Columns: date, item, issue, workaround, decision (configure, build or drop), role_or_surface, note. At least one item in 2 or more rows. | notebook step 6, then add your own rows by hand |
| `stage-11/change-evidence.csv` | before and after numbers for the one change you shipped | notebook step 7 |
| `stage-11/procurement-pack.md` | the buyer's questions, each answer linked to a file in your repo | you, from `templates/PROCUREMENT_PACK.md` |
| `stage-11/README.md` | your README (replace this checklist) | you |

## Your README must have

A section called **Decisions, Measures, and Next** that says:

- the customer setup you used (Northwind Learning, `data/customer_northwind/`, the three roles) and the model provider
- a link to the Stage 10 readout it builds on (`../stage-10/README.md`)
- the main deployment decisions (access map, prompt, retrieval k, what you dropped)
- the key counts from your real run: questions answered from the right page, leak test passes and fails per role, field log rows by tag
- the one repo change you shipped: the recurring field log item it fixes, the changed file paths, the commit hash, and one before and after (from `change-evidence.csv` or a screenshot of the app)
- what you would do next

## The one change

Pick a recurring item from `field-log.csv` (the `item` column shows which ones repeat). Step 7 shows one
example: an answer that always ends with "contact support" when no page answers. Put your change in a file
you commit (for example your answer function in `app/app.py`), rerun the notebook, and copy the commit
hash into your README.

## Procurement pack

Copy `templates/PROCUREMENT_PACK.md` to `stage-11/procurement-pack.md`. It covers the role leak test,
retention and redaction, the audit log of agent actions, your model provider's data terms (link their page),
and the AI disclosure users see. Link every answer to a file in your repo.

## Submit

The GitHub folder link to `stage-11/`.

Offline (`KIT_OFFLINE=1`) the notebook uses a mock model. Those numbers only show the notebook works. Run it live for the numbers in your README.
