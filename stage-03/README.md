# Stage 3: build and ship the first working assistant

Submit the GitHub repo link plus the live URL.

## Checklist

| File | What the brief asks for | How to make it |
| --- | --- | --- |
| `stage-03/README.md` | The Stage 2 failure you chose, why, what you changed, what you measured, the result, the next two improvements, and links to every evidence file | you, from the template below |
| `prompts/help_v1.md`, `help_v2.md` ... (repo root) | The system prompt in a versioned file | `app/app.py` loads `PROMPT_FILE`. Copy to a new version, never edit a used one |
| `.env` (untracked) | The API key, never committed | `GEMINI_API_KEY=...` in `.env`; git already ignores it |
| `stage-03/CODEMAP.md` | Five items with file path and line: app entry point, model call, prompt load, main config values, key loading | copy `CODEMAP.template.md`; find lines with `grep -n` |
| `stage-03/DEBUG.md` | Commit link for an AI assisted change to `scripts/call_model.py`, the traceback from a real failed run, the fix, and the fix commit link | copy `DEBUG.template.md` |
| `stage-03/MCP.md` | Pinned server version, rewritten tool description, tool list, scope list, MCP Inspector check with the date | copy `MCP.template.md`; `python mcp_server/describe.py` prints the facts |
| `stage-03/evals/retest_inputs.jsonl` | 10 inputs and the pass rule for the one Stage 2 failure you fixed | copy `evals/retest_inputs.example.jsonl` and edit |
| `stage-03/evals/retest_results.csv`, `retest_summary.md` | 10 inputs x 5 runs = 50 runs, pass count and pass rate, linked to the backlog item | `python scripts/retest.py --inputs stage-03/evals/retest_inputs.jsonl` |
| `stage-03/PRS.md` | 3 or more merged PR links, one line each on why it mattered | copy `PRS.template.md` |
| `stage-03/DEPLOYED.md` | URL, host, date deployed, spend cap on the key, and your EEA, Switzerland and UK choice | copy `DEPLOYED.template.md`; deploy steps in `app/README.md` |

## Steps

1. Fork the kit, clone it, and move your Stage 1 and 2 notebooks into `stage-01/` and `stage-02/`.
2. Pick one row of `stage-02/failure_backlog.csv` to fix. Write the pass rule and 10 inputs for it first.
3. Run `scripts/retest.py` before the fix to see it fail, make the fix with a free AI coding tool in a PR, then run it again.
   Each PR says what changed and how you checked it. Merge at least three.
4. Deploy (`app/README.md`). The live app must answer over your documents with page citations.
5. Use your own words in every file. Placeholders like `<your live URL>` must all be gone.

The kit example fix: billing questions cite the admin only refund page `qn-13`. Setting
`HIDE_VISIBILITY = ["admin"]` in `app/app.py` stops that, and `retest_inputs.example.jsonl` checks it.

## README template

```
## The Stage 2 failure I fixed
(backlog rank and label, link to stage-02/failure_backlog.csv)
## Why this one
## What I changed
(PR links, prompts/help_vN.md)
## What I measured
(link to evals/retest_summary.md and evals/retest_results.csv)
## Result
(pass count and pass rate out of 50)
## Next two improvements
## Evidence files
(CODEMAP.md, DEBUG.md, MCP.md, PRS.md, DEPLOYED.md, evals/)
```
