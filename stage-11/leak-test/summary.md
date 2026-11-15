# Leak test: Northwind roles

Run on 2026-11-15 with provider `mock`. Retrieval k = 5.

| Role | Prompts run | Passed | Failed | Raw output |
| --- | --- | --- | --- | --- |
| student | 16 | 16 | 0 | [raw-student.jsonl](raw-student.jsonl) |
| tutor | 16 | 16 | 0 | [raw-tutor.jsonl](raw-tutor.jsonl) |
| admin | 16 | 16 | 0 | [raw-admin.jsonl](raw-admin.jsonl) |

Control (filter off, as a student): 16 of 16 prompts leaked, as it should. Raw: [raw-control-no-filter.jsonl](raw-control-no-filter.jsonl)
