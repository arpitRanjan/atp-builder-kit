# Example stage 3 (offline mock model)

The re-test files in `evals/` are real runs of `scripts/retest.py` with the offline mock model
(`KIT_OFFLINE=1`): `evals/before/` on the kit app, `evals/` on this example's `app/app.py` and
`prompts/help_v2.md`. The numbers are not real model results. The traceback in `DEBUG.md` is from a real
run of the kit's `scripts/call_model.py` with no key set.

Files outside `stage-03/` in this example: `app/app.py`, `prompts/help_v1.md`, `prompts/help_v2.md`,
`mcp_server/server.py` and `scripts/call_model.py`, each with the example change.

What a learner must still do themselves:

- Pick their own Stage 2 failure, write its 10 inputs and pass rule, and run the re-test with a real key.
- Make the changes with a free AI coding tool, in 3 or more merged PRs, and fill in every `<PR link>` and `<commit link>`.
- Deploy the app and fill in `DEPLOYED.md` (`<your live URL>`, host, date, spend cap, EEA, Switzerland and UK choice).
- Check the MCP server in MCP Inspector and write the date in `MCP.md`.
- Keep the key in an untracked `.env`. The live app must answer over their documents with citations.
