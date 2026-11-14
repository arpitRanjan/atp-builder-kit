# The same help-assistant call as notebook 01, but with plain HTTP (requests) to the Gemini REST API.
# Run:  python scripts/call_model.py        Offline (no network):  KIT_OFFLINE=1 python scripts/call_model.py
import csv
import json
import os
from pathlib import Path

import requests

# Settings you can change.
MODEL = "gemini-3.5-flash-lite"
URL = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent"
HERE = Path(__file__).resolve().parent
OUT = HERE / "runs.csv"

# The request body: a system prompt, the user question, temperature and an output cap.
body = {
    "systemInstruction": {"parts": [{"text": "You are the help assistant for Quillnote, a note app. Be brief."}]},
    "contents": [{"role": "user", "parts": [{"text": "How do I export a note as PDF?"}]}],
    "generationConfig": {"temperature": 0.2, "maxOutputTokens": 200},
}


def call_once():
    # Offline mode reads a saved response instead of calling the API.
    if os.environ.get("KIT_OFFLINE") == "1":
        return json.loads((HERE / "sample_response.json").read_text())
    key = os.environ["GEMINI_API_KEY"]
    resp = requests.post(URL, headers={"x-goog-api-key": key}, json=body, timeout=60)
    resp.raise_for_status()
    return resp.json()


# One call: print the raw JSON so you can see its shape.
data = call_once()
print(json.dumps(data, indent=2))

# Pull out the parts we care about.
def summarise(data):
    cand = data["candidates"][0]
    usage = data["usageMetadata"]
    return {
        "text": cand["content"]["parts"][0]["text"],
        "input_tokens": usage["promptTokenCount"],
        "output_tokens": usage.get("candidatesTokenCount", 0),
        "finish_reason": cand["finishReason"],
    }


print(summarise(data))

# Run 10 times and save each result as a row in runs.csv.
with open(OUT, "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=["run", "input_tokens", "output_tokens", "finish_reason", "text"])
    writer.writeheader()
    for run in range(1, 11):
        writer.writerow({"run": run, **summarise(call_once())})

# Read the file back and print the average output tokens.
with open(OUT) as f:
    rows = list(csv.DictReader(f))
average = sum(int(r["output_tokens"]) for r in rows) / len(rows)
print(f"{len(rows)} runs saved to {OUT.name}. Average output tokens: {average:.1f}")

# ---------- Break it on purpose ----------
# Practise reading a traceback. Try one change at a time, run, read the LAST line of the error first.
# 1. Rename the env var: change os.environ["GEMINI_API_KEY"] to os.environ["GEMINI_KEY"].
#    You get KeyError: 'GEMINI_KEY'. The traceback points at the line that read it.
# 2. Ask for a field that does not exist: change usage["promptTokenCount"] to usage["promptTokens"].
#    You get KeyError: 'promptTokens'. Compare with the raw JSON printed above to find the real name.
