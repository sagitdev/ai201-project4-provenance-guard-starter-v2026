#!/usr/bin/env python3
"""
Criterion 5 — one trial: 5 appeals against a log padded to a year's size.

No gunicorn needed. The padded log is a temporary copy; the real log is only
read, never written.

    python capstone_c5.py 1        # trial number: 1, 2 or 3

Writes results/capstone_c5_trial<k>.json and refuses to overwrite it.
"""

import json
import sys
import tempfile
import time
import uuid
from pathlib import Path

import config

TARGET_LINES = 46_000 # 每天 100 次提交 × 365 天 = 36,500 条判定; 按第 415–443 行的比例（每 29 行有 23 条判定）：36,500 × 29 ÷ 23 ≈ 46,000 行     
TARGET_MS = 1_000

trial = int(sys.argv[1])
# out = Path("results") / f"capstone_c5_trial{trial}.json"
suffix = f"_{sys.argv[2]}" if len(sys.argv) > 2 else ""
out = Path("results") / f"capstone_c5{suffix}_trial{trial}.json"
if out.exists():
    sys.exit(f"{out} already exists. Results are evidence; not overwriting.")

# 1. Build the padded copy.
real = config.AUDIT_LOG.read_text(encoding="utf-8").splitlines()
block = real[414:443]            # lines 415-443, counted from 1
if len(block) != 29:
    sys.exit(f"Expected 29 lines in 415-443, got {len(block)}.")

padded = list(real)
while len(padded) < TARGET_LINES:
    for line in block:
        if len(padded) >= TARGET_LINES:
            break
        entry = json.loads(line)
        if entry.get("status") == "decided":
            entry["content_id"] = str(uuid.uuid4())
        padded.append(json.dumps(entry, ensure_ascii=False))

scratch = Path(tempfile.mkdtemp(prefix="capstone_c5_"))
config.LOG_DIR = scratch
config.AUDIT_LOG = scratch / "audit.jsonl"
config.AUDIT_LOG.write_text("\n".join(padded) + "\n", encoding="utf-8")
size_bytes = config.AUDIT_LOG.stat().st_size

import app as svc   # noqa: E402  (imported after the log is redirected)
import audit        # noqa: E402

client = svc.app.test_client()

# 2. Five decisions, evenly spaced through the padded log.
decisions = [json.loads(line) for line in padded if '"status": "decided"' in line]
step = len(decisions) // 5
targets = [decisions[i * step] for i in range(5)]

# 3. One valid appeal against each.
rows = []
for n, d in enumerate(targets, start=1):
    t = time.perf_counter()
    r = client.post("/appeal", json={
        "content_id": d["content_id"],
        "creator_id": d["creator_id"],
        "reasoning": "I wrote this myself.",
        "attestation": True,
    })
    client_ms = round((time.perf_counter() - t) * 1000, 1)
    record = audit.read_entries(limit=1)[0]      # the appeal line it just wrote
    duration_ms = record.get("duration_ms") if record.get("event") == "appeal" else None
    rows.append({
        "appeal": n,
        "content_id": d["content_id"],
        "status_code": r.status_code,
        "duration_ms": duration_ms,
        "client_ms": client_ms,
        "ok": r.status_code == 200 and duration_ms is not None and duration_ms <= TARGET_MS,
    })

met = all(row["ok"] for row in rows)
result = {
    "criterion": 5,
    "trial": trial,
    "padded_lines": len(padded),
    "padded_bytes": size_bytes,
    "decisions_in_log": len(decisions),
    "slowest_duration_ms": max((row["duration_ms"] or 0) for row in rows),
    "met": met,
    "rows": rows,
}
out.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

print(f"trial {trial}: padded log {len(padded):,} lines, {size_bytes / 1e6:.1f} MB, "
      f"{len(decisions):,} decisions")
for row in rows:
    print(f"  appeal {row['appeal']}  status {row['status_code']}  "
          f"duration {row['duration_ms']} ms  client {row['client_ms']} ms  "
          f"{'PASS' if row['ok'] else 'FAIL'}")
print(f"  -> {'MET' if met else 'MISSED'} this trial   (saved to {out})")