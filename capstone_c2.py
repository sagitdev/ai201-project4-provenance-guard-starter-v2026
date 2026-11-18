#!/usr/bin/env python3
"""
Criterion 2 — one trial: four forced failures in a test process.

No gunicorn needed. Everything runs in this process with app.test_client(),
and config.AUDIT_LOG points at a temporary file, so the real log is untouched.

    python capstone_c2.py 1        # trial number: 1, 2 or 3

Writes results/capstone_c2_trial<k>.json and refuses to overwrite it.
"""

import json
import logging
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import config

trial = int(sys.argv[1])
out = Path("results") / f"capstone_c2_trial{trial}.json"
if out.exists():
    sys.exit(f"{out} already exists. Results are evidence; not overwriting.")

# Point the log at a temporary file BEFORE anything writes to it.
scratch = Path(tempfile.mkdtemp(prefix="capstone_c2_"))
config.LOG_DIR = scratch
config.AUDIT_LOG = scratch / "audit.jsonl"

import app as svc   # noqa: E402  (imported after the log is redirected)
import audit        # noqa: E402
from capstone_texts import TEXTS, key  # noqa: E402

client = svc.app.test_client()
tc = unittest.TestCase()
TEXT = TEXTS[key("#2")]

FAULTS = [
    ("a. model signal", "detector.model_signal",   RuntimeError("simulated model failure")),
    ("b. style signal", "stylometry.style_signal", RuntimeError("simulated style failure")),
    ("c. combining",    "scoring.combine_signals", RuntimeError("simulated combine failure")),
    ("d. log write",    "audit._append",           OSError(28, "No space left on device")),
]

rows = []
for n, (name, target, exc) in enumerate(FAULTS, start=1):
    before = len(audit.read_entries())
    logged = ""
    try:
        with mock.patch(target, side_effect=exc):
            try:
                with tc.assertLogs(svc.app.logger, level="ERROR") as cm:
                    r = client.post("/submit", json={"creator_id": f"m5_c2_t{trial}_f{n}", "text": TEXT})
                logged = "\n".join(logging.Formatter().format(rec) for rec in cm.records)
            except AssertionError:      # assertLogs: nothing was logged at all
                r = client.post("/submit", json={"creator_id": f"m5_c2_t{trial}_f{n}b", "text": TEXT})
        status, body, error = r.status_code, r.get_json(silent=True), None
    except Exception as e:      # the request escaped every handler
        status, body, error = None, None, f"{type(e).__name__}: {e}"

    new = audit.read_entries()[before:]

    # After the fault, the real function is back. Is the service still usable?
    follow = client.post("/submit", json={"creator_id": f"m5_c2_t{trial}_ok{n}", "text": TEXT})

    is_json = isinstance(body, dict)
    checks = {
        "status_500": status == 500,
        "json_error_and_message": is_json and "error" in body and "message" in body,
        "no_content_id": not (is_json and "content_id" in body),
        "follow_up_200": follow.status_code == 200,
    }
    if target != "audit._append":
        # a, b, c: exactly one error record in the log
        errors = [e for e in new if e.get("event") == "error"]
        checks["one_error_record"] = (
            len(new) == 1 and len(errors) == 1
            and "error_type" in errors[0]
            and errors[0].get("http_status") == 500
            and isinstance(errors[0].get("duration_ms"), (int, float))
        )
    else:
        # d: the log can't be written, so the logger is the only witness
        checks["logger_shows_oserror"] = "OSError" in logged

    rows.append({
        "fault": name,
        "patched": target,
        "status_code": status,
        "content_type": r.content_type if error is None else None,
        "body": body,
        "error": error,
        "new_log_lines": new,
        "logger_mentions": [line for line in logged.splitlines() if "Error" in line][:5],
        "follow_up_status": follow.status_code,
        "checks": checks,
        "ok": all(checks.values()),
    })

met = all(row["ok"] for row in rows)
result = {"criterion": 2, "trial": trial, "scratch_log": str(config.AUDIT_LOG),
          "met": met, "rows": rows}
out.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

print(f"trial {trial}")
for row in rows:
    print(f"  {row['fault']:16} status {row['status_code']}  {row['content_type']}")
    for name, ok in row["checks"].items():
        print(f"      {'PASS' if ok else 'FAIL'}  {name}")
print(f"  -> {'MET' if met else 'MISSED'} this trial   (saved to {out})")