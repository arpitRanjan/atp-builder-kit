# Example stage 13

Made with the offline mock model (`KIT_OFFLINE=1`). The numbers are not real model results: the mock obeys any
instruction it reads in a page, so it shows the worst case, and its latencies are made up. Nothing in `outbox.jsonl`
was sent anywhere. The injected pages are copies in `injected-docs/`; `corpus/` was never changed.

Every file here came from running both `13` notebooks with `KIT_OUTPUT_DIR` set to `stage-13/`, except `README.md`,
written by hand from that run.

You still have to do yourself:
- run both notebooks live and replace every number in `README.md`
- call `guarded_answer` from your app's answer path and fill in the file and commit
- qualify a real fallback model (a second provider or a smaller model)
