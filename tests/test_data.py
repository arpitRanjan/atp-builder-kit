# (a) The data script runs and the three planted traps are really there.
import csv
import json
import subprocess
import sys
from collections import Counter

from conftest import ROOT


def test_make_data_has_traps(tmp_path):
    subprocess.run([sys.executable, str(ROOT / "data" / "make_data.py"), "--out", str(tmp_path)], check=True)
    users = list(csv.DictReader(open(tmp_path / "users.csv")))
    events = list(csv.DictReader(open(tmp_path / "events.csv")))
    # Trap 1: some users have several plan rows, so a join fans out.
    assert max(Counter(u["user_id"] for u in users).values()) > 1
    # Trap 2: some plan values are NULL (empty).
    assert any(u["plan"] == "" for u in users)
    # Trap 3: events at exactly midnight UTC on Nov 1, and many later on Oct 31.
    assert any(e["event_ts"] == "2026-11-01 00:00:00" for e in events)
    assert sum(e["event_ts"].startswith("2026-10-31") for e in events) > 300
    traces = [json.loads(line) for line in open(tmp_path / "traces.jsonl")]
    assert 590 <= len(traces) <= 630 and any(t["pii_planted"] for t in traces)


def test_generated_files_match_committed(tmp_path):
    # Fixed seed: regenerating gives the same files that are committed.
    subprocess.run([sys.executable, str(ROOT / "data" / "make_data.py"), "--out", str(tmp_path)], check=True)
    for name in ["users.csv", "events.csv", "traces.jsonl", "holdout.csv"]:
        assert (tmp_path / name).read_bytes() == (ROOT / "data" / name).read_bytes(), name
