# The handover bundle: anyone can run these cold, from the kit folder, with no notebook open.
# Add KIT_OFFLINE=1 in front to use the mock model, for example: KIT_OFFLINE=1 make evals
PYTHON ?= python

.PHONY: evals traces test

evals:  ## run the golden set eval suite in one command (exit 1 if a hard gate fails)
	$(PYTHON) evals/run_evals.py

traces:  ## send 20 traced requests and export traces/spans.jsonl and traces/spans.csv
	$(PYTHON) -m kit.tracing --requests 20 --out traces/spans.jsonl

test:  ## the offline test suite
	KIT_OFFLINE=1 $(PYTHON) -m pytest -q
