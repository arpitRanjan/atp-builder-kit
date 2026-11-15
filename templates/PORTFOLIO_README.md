# <Your product name>

<!-- Use this as the top of your root README.md. A hiring manager should get it in about two minutes. -->

[![evals](https://github.com/<you>/atp-builder-kit/actions/workflows/evals.yml/badge.svg?branch=main)](https://github.com/<you>/atp-builder-kit/actions/workflows/evals.yml)

**Live app:** <your live URL>

## What it does

<Two sentences: what the product does and what it answers from.>

## Who it is for

<The user, and the job they hire it for.>

## How quality is checked

- Golden set and hard gates run on every pull request (`evals/`, `.github/workflows/evals.yml`). Latest green run: <link>.
- Regression set with red team attacks (`evals/regression.jsonl`). pass^3: <number>.
- Guardrails: input and output checks, rate limit, spend cap, host allowlist (`kit/guardrails.py`).

## Current limits

- <one honest limit, for example: Spanish answers are on hold (stage 12)>
- <another>

## Take-home and system design recording

- Take-home: [stage-15/TAKEHOME.md](stage-15/TAKEHOME.md), shipped in <PR link>
- System design recording (25 to 35 minutes): <recording link>, chapters in [stage-15/README.md](stage-15/README.md)

## Built in 15 stages

Each `stage-NN/` folder holds one stage of the build, from baseline runs to this take-home.
