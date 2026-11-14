"""Make the kit's synthetic data. Everything here is invented. Same seed, same files every time.

Run:  python data/make_data.py            (writes into data/)
      python data/make_data.py --out DIR  (writes somewhere else)

Planted traps (the SQL notebook finds them):
  1. Fan-out join: some users have several rows in users.csv (one per plan change).
  2. NULL plans: some plan values are empty, so WHERE plan <> 'free' silently drops them.
  3. Midnight boundary: many events on 2026-10-31 and some at exactly 2026-11-01 00:00:00 UTC.
"""
import argparse
import csv
import json
import random
from datetime import datetime, timedelta
from pathlib import Path

SEED = 42
N_USERS = 800
COUNTRIES = ["US", "IN", "DE", "BR", "GB", "JP"]
PLANS = ["free", "pro", "team"]
EVENTS = ["note_created", "search", "share", "export", "upgrade_click"]


def make_users(rng):
    rows = []
    for uid in range(1, N_USERS + 1):
        signup = datetime(2026, 9, 1) + timedelta(days=rng.randint(0, 45))
        plan = rng.choices(PLANS, weights=[70, 20, 10])[0]
        if rng.random() < 0.08:
            plan = ""  # trap 2: NULL plan
        rows.append([uid, signup.date().isoformat(), rng.choice(COUNTRIES), plan, signup.date().isoformat()])
        if rng.random() < 0.15:  # trap 1: a second (and sometimes third) plan row for the same user
            for k in range(rng.choice([1, 1, 2])):
                start = signup + timedelta(days=10 * (k + 1))
                rows.append([uid, signup.date().isoformat(), rows[-1][2], rng.choice(["pro", "team"]),
                             start.date().isoformat()])
    return ["user_id", "signup_date", "country", "plan", "plan_start"], rows


def make_events(rng):
    rows, eid = [], 1
    for uid in range(1, N_USERS + 1):
        for _ in range(rng.randint(3, 25)):
            ts = datetime(2026, 10, 1) + timedelta(seconds=rng.randint(0, 40 * 86400))
            rows.append([eid, uid, ts.strftime("%Y-%m-%d %H:%M:%S"), rng.choice(EVENTS)])
            eid += 1
    for _ in range(300):  # trap 3: a busy last day of October
        ts = datetime(2026, 10, 31) + timedelta(seconds=rng.randint(1, 86399))
        rows.append([eid, rng.randint(1, N_USERS), ts.strftime("%Y-%m-%d %H:%M:%S"), rng.choice(EVENTS)])
        eid += 1
    for _ in range(40):  # trap 3: events at exactly midnight UTC on Nov 1 (they belong to November)
        rows.append([eid, rng.randint(1, N_USERS), "2026-11-01 00:00:00", rng.choice(EVENTS)])
        eid += 1
    return ["event_id", "user_id", "event_ts", "event_name"], rows


MESSAGES = [
    "How do I export a note as PDF?", "My notes stopped syncing", "Can I share a notebook with my team?",
    "How do I undo a deleted note?", "Where is dark mode?", "Can I search inside images?",
    "Why was I charged twice?", "How do I add a tag?", "The app crashes when I open a big note",
]


def fake_pii(rng):
    # Some PII is in easy formats, some in formats simple regexes miss.
    n = rng.randint(1000, 9999)
    return rng.choice([
        f"user{n}@example.com", f"+1 555-{n // 10:03d}-{n}", f"4111 1111 1111 {n}",
        f"555.{n // 10:03d}.{n}", f"user{n} at example dot com", f"4111-1111-1111-{n}",
    ])


def make_traces(rng):
    rows = []
    for i in range(1, 601):
        segment = rng.choice(["free", "pro", "team"])
        channel = rng.choice(["web", "ios", "android"])
        msg = rng.choice(MESSAGES)
        pii = [fake_pii(rng) for _ in range(rng.choice([0, 0, 1, 2]))]
        if pii:
            msg += " My details: " + ", ".join(pii)
        fail_rate = 0.55 if (segment == "team" and channel == "android") else 0.12  # the failing cohort
        outcome = "failed" if rng.random() < fail_rate else rng.choice(["resolved", "resolved", "escalated"])
        output = "Sorry, something went wrong." if outcome == "failed" else f"Here is how: {msg[:30]}..."
        if rng.random() < 0.03:
            output = ""  # empty output
        rows.append({
            "trace_id": f"t{i:04d}", "timestamp": f"2026-10-{rng.randint(1, 31):02d}T{rng.randint(0, 23):02d}:00:00Z",
            "user_id": f"test_{i}" if rng.random() < 0.04 else f"u{rng.randint(1, N_USERS)}",
            "segment": segment, "channel": channel, "user_message": msg, "assistant_output": output,
            "outcome": outcome, "latency_ms": rng.randint(300, 9000), "cost_usd": round(rng.uniform(0.0002, 0.004), 5),
            "pii_planted": pii,
        })
    rows += [dict(rows[j]) for j in rng.sample(range(600), 15)]  # exact duplicates
    return rows


def make_holdout(rng):
    # Treatment wins on BOTH platforms, but it got far more mobile users (low baseline): a mix shift.
    rows, uid = [], 1
    plan = {("control", "desktop"): (1400, 0.20), ("control", "mobile"): (600, 0.05),
            ("treatment", "desktop"): (600, 0.23), ("treatment", "mobile"): (1400, 0.06)}
    for (arm, platform), (n, rate) in plan.items():
        for _ in range(n):
            rows.append([uid, arm, platform, int(rng.random() < rate)])
            uid += 1
    return ["user_id", "arm", "platform", "converted"], rows


def write_csv(path, header, rows):
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)


def main(out):
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    rng = random.Random(SEED)
    write_csv(out / "users.csv", *make_users(rng))
    write_csv(out / "events.csv", *make_events(rng))
    with open(out / "traces.jsonl", "w") as f:
        for row in make_traces(rng):
            f.write(json.dumps(row) + "\n")
    write_csv(out / "holdout.csv", *make_holdout(rng))
    print(f"Wrote users.csv, events.csv, traces.jsonl, holdout.csv to {out}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default=str(Path(__file__).resolve().parent))
    main(parser.parse_args().out)
