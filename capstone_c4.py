#!/usr/bin/env python3
"""
Criterion 4 — one warm-latency trial: 12 texts in four length groups.

The service must already be running (see RUNNING.md). It doesn't need a
restart: this script sends a warm-up request first.

    python capstone_c4.py 1        # trial number: 1, 2 or 3

Writes results/capstone_c4_trial<k>.json and refuses to overwrite it.
"""

import json
import sys
import time
from pathlib import Path

import requests

import audit
from capstone_texts import GROUPS

BASE = "http://127.0.0.1:5000"
CLIENT_TARGET_MS = 1_000   # A: what the writer waits
GAP_TARGET_MS = 50         # B: how far the log may be from that

trial = int(sys.argv[1])
# out = Path("results") / f"capstone_c4_trial{trial}.json"
suffix = f"_{sys.argv[2]}" if len(sys.argv) > 2 else ""
out = Path("results") / f"capstone_c4{suffix}_trial{trial}.json"
if out.exists():
    sys.exit(f"{out} already exists. Results are evidence; not overwriting.")


def send(creator_id, text):
    """One /submit: client time, status, and the log line it wrote."""
    before = len(audit.read_entries())
    t = time.perf_counter()
    try:
        r = requests.post(BASE + "/submit",
                          json={"creator_id": creator_id, "text": text}, timeout=60)
        status_code, error = r.status_code, None
    except requests.RequestException as exc:
        status_code, error = None, f"{type(exc).__name__}: {exc}"
    client_ms = round((time.perf_counter() - t) * 1000, 1)
    new = audit.read_entries()[before:]
    record = new[0] if len(new) == 1 else {}
    return status_code, error, client_ms, len(new), record


# 1. Warm-up, then make sure the model really is loaded.
send(f"m5_c4_t{trial}_warmup", GROUPS["100w"][0])
if not requests.get(BASE + "/health", timeout=5).json()["detector_loaded"]:
    sys.exit("GPT-2 still isn't loaded after the warm-up; this wouldn't be a warm trial.")

# 2. The 12 texts, in order, each with its own creator_id.
rows = []
for group, texts in GROUPS.items():
    for i, text in enumerate(texts, start=1):
        status_code, error, client_ms, new_lines, record = send(
            f"m5_c4_t{trial}_{group}_{i}", text)
        duration_ms = record.get("duration_ms")
        valid = status_code == 200 and new_lines == 1 and duration_ms is not None
        gap_ms = round(client_ms - duration_ms, 1) if valid else None
        rows.append({
            "group": group,
            "text": i,
            "chars": len(text),
            "status_code": status_code,
            "error": error,
            "new_lines": new_lines,
            "client_ms": client_ms,
            "duration_ms": duration_ms,
            "stage_ms": record.get("stage_ms"),
            "gap_ms": gap_ms,
            "valid": valid,
            "a_ok": valid and client_ms <= CLIENT_TARGET_MS,
            "b_ok": valid and gap_ms <= GAP_TARGET_MS,
        })

# 3. The verdict for this trial.
a_met = all(row["a_ok"] for row in rows)
b_met = all(row["b_ok"] for row in rows)
met = a_met and b_met

result = {
    "criterion": 4,
    "trial": trial,
    "slowest_client_ms": max(row["client_ms"] for row in rows),
    "largest_gap_ms": max((row["gap_ms"] for row in rows if row["gap_ms"] is not None), default=None),
    "a_met": a_met,
    "b_met": b_met,
    "met": met,
    "rows": rows,
}
out.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

print(f"trial {trial}")
print(f"  {'group':6} {'#':>2} {'status':>6} {'client':>9} {'duration':>9} {'gap':>6}  model ms")
for row in rows:
    model = (row["stage_ms"] or {}).get("model")
    print(f"  {row['group']:6} {row['text']:>2} {str(row['status_code']):>6} "
          f"{row['client_ms']:>9} {str(row['duration_ms']):>9} {str(row['gap_ms']):>6}  {model}")
print(f"  A (all client ≤ {CLIENT_TARGET_MS} ms): {'PASS' if a_met else 'FAIL'}"
      f"   slowest {result['slowest_client_ms']} ms")
print(f"  B (all gaps ≤ {GAP_TARGET_MS} ms):      {'PASS' if b_met else 'FAIL'}"
      f"   largest {result['largest_gap_ms']} ms")
print(f"  -> {'MET' if met else 'MISSED'} this trial   (saved to {out})")