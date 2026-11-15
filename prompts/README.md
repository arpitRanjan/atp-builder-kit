# prompts

Every system prompt the app uses lives here as a versioned file: `help_v1.md`, `help_v2.md`, and so on.
Never edit a version in place once it has been used. Copy it to the next number, change the copy,
then point `PROMPT_FILE` in `app/app.py` at the new file. The whole file is the prompt text.
Approve each version in `prompts/APPROVALS.md` with the eval run that approved it (see `stage-08/README.md`).
