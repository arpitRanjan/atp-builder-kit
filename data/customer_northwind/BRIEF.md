# Customer brief: Northwind Learning (simulated)

Northwind Learning is an invented company for practice. It is a small online tutoring firm, not a real
business. Everything in this folder is made up for the course.

## Who they are

- About 40 tutors and 900 students, mostly high school maths and science.
- Lessons run as video calls booked through the Northwind web app.
- Support today is two people answering email. Most questions repeat every week.

## What they want

A help assistant inside their app that answers from their own help pages, so students and tutors get
an answer in seconds and the support team keeps only the hard cases.

## Who uses it (three roles)

| Role | Who | May read |
| --- | --- | --- |
| student | a learner or their parent | student pages |
| tutor | a tutor on contract | student and tutor pages |
| admin | the support and operations team | every page |

Tutor pay and admin procedures must never reach a student. Safeguarding pages are admin only.

## Constraints

- Pilot of 4 weeks, with 5 tutors and about 60 students.
- They will not share real student data. Test with their help pages only (the 10 in `pages/`).
- Answers must say "contact support" when the pages do not cover the question.

## How they will judge the pilot

- At least 70 percent of student questions answered from the pages without a support email.
- Zero leaks: no tutor or admin page shown to a student, checked every week.
- Support email volume down by a quarter by week 4.

## Field log

Write every configuration choice, issue and workaround in `stage-11/field-log.csv` (date, item, issue, workaround,
decision, role_or_surface, note). The decision is one of `configure` (change settings or content), `build` (a product
change) or `drop` (not worth it). Use the same `item` text for rows about the same thing, so recurring items show up.
