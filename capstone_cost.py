#!/usr/bin/env python3
"""
Capstone M3 — what one run costs, read back from the audit log.

    python capstone_cost.py

Cost here is seconds of compute: each decision's duration_ms, the time from
the request arriving to just before its log line is written, on one gunicorn
worker (wall-clock, CPU only). Nothing is estimated; every number comes from
logs/audit.jsonl.
"""

import statistics

import audit

# Only the M3 session's distinct texts. The flood requests repeat one short
# text, so counting them would pull the average down.
PREFIX = "m3_run_"
USERS_PER_DAY = 100


def summary(name, ms):
    """Print count, mean, min and max for a list of milliseconds."""
    print(f"{name:6} n={len(ms):3}  mean {statistics.mean(ms):8.1f} ms"
          f"  min {min(ms):8.1f}  max {max(ms):8.1f}")


entries = audit.read_entries()

# 1. Capstone-format decisions from this session only.
decisions = [
    e for e in entries
    if e.get("status") == "decided"
    and "duration_ms" in e
    and str(e.get("creator_id", "")).startswith(PREFIX)
]

# 2. Split by whether GPT-2 was already loaded when the request arrived.
cold = [e["duration_ms"] for e in decisions if not e["model_was_loaded"]]
warm = [e["duration_ms"] for e in decisions if e["model_was_loaded"]]

if not cold or not warm:
    raise SystemExit(f"No cold or warm decisions matched PREFIX={PREFIX!r}. Check the filter.")
summary("cold", cold)
summary("warm", warm)

# 3. Per run, in seconds.
warm_s = statistics.mean(warm) / 1000
cold_s = statistics.mean(cold) / 1000
print(f"\nOne warm run: {warm_s:.4f} s   one cold start: {cold_s:.3f} s"
      f"   (cold ≈ {cold_s / warm_s:.0f}× warm)")

# 4. A hundred people a day, one submission each.
a = USERS_PER_DAY * warm_s
b = cold_s + (USERS_PER_DAY - 1) * warm_s
worst = USERS_PER_DAY * cold_s

print(f"\nA. always running, all warm:    {USERS_PER_DAY} × {warm_s:.4f} = {a:.2f} s/day")
print(f"B. one restart a day:           {cold_s:.3f} + {USERS_PER_DAY - 1} × {warm_s:.4f} = {b:.2f} s/day")
print(f"Worst case, every request cold: {USERS_PER_DAY} × {cold_s:.3f} = {worst:.1f} s/day")