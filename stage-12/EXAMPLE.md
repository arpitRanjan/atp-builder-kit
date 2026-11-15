# Example stage 12

Made with the offline mock model (`KIT_OFFLINE=1`). The numbers are not real model results: the translator is a
word list and the judge is a word overlap rule (`kit/mock_brain.py`). The 100 percent variant score comes from that word list.

Every file here came from running `notebooks/12_locale_eval.ipynb` with `KIT_OUTPUT_DIR` set to `stage-12/`, except
`README.md` (written by hand) and `.github/workflows/evals.yml` (the Stage 8 workflow plus the Spanish step).

You still have to do yourself:
- run it live and replace every number in `README.md`
- open a pull request so the Spanish step runs in CI, and link that run
- make your own readiness call
