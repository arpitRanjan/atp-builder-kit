# (c) scripts/call_model.py runs offline and writes runs.csv.
import os
import subprocess
import sys

from conftest import ROOT


def test_call_model_offline():
    env = {**os.environ, "KIT_OFFLINE": "1"}
    env.pop("GEMINI_API_KEY", None)
    out = subprocess.run([sys.executable, str(ROOT / "scripts" / "call_model.py")], env=env,
                         capture_output=True, text=True, check=True).stdout
    assert "Average output tokens: 27.0" in out
    assert (ROOT / "scripts" / "runs.csv").exists()
