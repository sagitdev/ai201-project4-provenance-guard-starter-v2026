#!/usr/bin/env python3
"""
Criterion 3 — one cold-start trial.

Before each trial, by hand (see criteria.md, criterion 3):
    1. stop the service; `lsof -nP -iTCP:5000 -sTCP:LISTEN` prints nothing
    2. sudo purge
    3. gunicorn app:app --bind 127.0.0.1:5000 --workers 1
    4. wait until /ping answers

Then:
    python capstone_c3.py 1        # trial number: 1, 2 or 3

Writes results/capstone_c3_trial<k>.json and refuses to overwrite it.
"""

import json
import sys
import time
from pathlib import Path

import requests

import audit
from capstone_texts import COLD_START_TEXT

BASE = "http://127.0.0.1:5000"
TARGET_MS = 15_000

trial = int(sys.argv[1])
# out = Path("results") / f"capstone_c3_trial{trial}.json"
suffix = f"_{sys.argv[2]}" if len(sys.argv) > 2 else ""
out = Path("results") / f"capstone_c3{suffix}_trial{trial}.json"
if out.exists():
    sys.exit(f"{out} already exists. Results are evidence; not overwriting.")

# 1. Is this really a cold start?
health = requests.get(BASE + "/health", timeout=5).json()
if health["detector_loaded"]:
    sys.exit("GPT-2 is already loaded, so this wouldn't be a cold start. Restart first.")

# 2. How long is the log before?
before = len(audit.read_entries())

# 3. The cold-start submission.
t = time.perf_counter()
try:
    r = requests.post(
        BASE + "/submit",
        json={"creator_id": f"m5_c3_t{trial}", "text": COLD_START_TEXT},
        timeout=60,
    )
    status_code = r.status_code
    error = None
except requests.RequestException as exc:
    status_code = None
    error = f"{type(exc).__name__}: {exc}"
client_ms = round((time.perf_counter() - t) * 1000, 1)

# 4. Exactly one new line?
new = audit.read_entries()[before:]
record = new[0] if len(new) == 1 else {}

# 5. The three checks from criteria.md.
checks = {
    "one_new_line": len(new) == 1,
    "status_200": status_code == 200,
    "model_was_loaded_false": record.get("model_was_loaded") is False,
    "duration_within_target": record.get("duration_ms") is not None
                              and record["duration_ms"] <= TARGET_MS,
}
met = all(checks.values())

result = {
    "criterion": 3,
    "trial": trial,
    "status_code": status_code,
    "new_lines": len(new),
    "error": error,
    "client_ms": client_ms,
    "record": record,
    "checks": checks,
    "met": met,
}
out.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

print(f"trial {trial}: status {status_code}  duration_ms {record.get('duration_ms')}  "
      f"client {client_ms} ms  model_was_loaded {record.get('model_was_loaded')}")
for name, ok in checks.items():
    print(f"  {'PASS' if ok else 'FAIL'}  {name}")
print(f"  -> {'MET' if met else 'MISSED'} this trial   (saved to {out})")