#!/usr/bin/env python3
"""
Criterion 1 — one trial: 24 requests, each must leave exactly one complete
timing record, and no submitted text may appear in the log.

Before each trial, by hand (see criteria.md, criterion 1):
    1. stop the service; `lsof -nP -iTCP:5000 -sTCP:LISTEN` prints nothing
    2. gunicorn app:app --bind 127.0.0.1:5000 --workers 1
    3. wait until /ping answers (don't send anything else)

Then:
    python capstone_c1.py 1        # trial number: 1, 2 or 3

Writes results/capstone_c1_trial<k>.json and refuses to overwrite it.
"""

import json
import sys
from pathlib import Path

import requests

import audit
from capstone_texts import TEXTS, key

BASE = "http://127.0.0.1:5000"
JSON_HEADER = {"Content-Type": "application/json"}

trial = int(sys.argv[1])
out = Path("results") / f"capstone_c1_trial{trial}.json"
if out.exists():
    sys.exit(f"{out} already exists. Results are evidence; not overwriting.")

if requests.get(BASE + "/health", timeout=5).json()["detector_loaded"]:
    sys.exit("GPT-2 is already loaded, so the first submission wouldn't be a cold start. Restart first.")

# The texts. Six different ones for the normal submissions, one more for the
# repeats, and a 50,001-character one that must be refused.
NORMAL = [TEXTS[key(s)] for s in ["#2", "#3", "#4", "#5", "#6", "#7"]]
REPEAT = TEXTS[key("#9")]
TOO_LONG = ((TEXTS[key("#1")] + " ") * 200)[:50_001]

# ─── Requests 1-20: submissions ──────────────────────────────────────────────
PLAN = []
for i, text in enumerate(NORMAL, start=1):
    PLAN.append((f"normal {i}", "/submit",
                 {"json": {"creator_id": f"m5_c1_t{trial}_n{i}", "text": text}}, 200))

PLAN += [
    ("bad: not JSON",     "/submit", {"data": "not json", "headers": JSON_HEADER}, 400),
    ("bad: JSON list",    "/submit", {"json": ["a", "list"]}, 400),
    ("bad: no creator_id", "/submit", {"json": {"text": "A body with no creator id."}}, 400),
    ("bad: no text",      "/submit", {"json": {"creator_id": "m5_bad"}}, 400),
    ("bad: spaces only",  "/submit", {"json": {"creator_id": "m5_bad", "text": "     "}}, 400),
    ("bad: 3 words",      "/submit", {"json": {"creator_id": "m5_bad", "text": "only three words"}}, 400),
    ("bad: 50,001 chars", "/submit", {"json": {"creator_id": "m5_bad", "text": TOO_LONG}}, 400),
]

for n in range(1, 8):
    PLAN.append((f"repeat {n}", "/submit",
                 {"json": {"creator_id": f"m5_c1_t{trial}_repeat", "text": REPEAT}},
                 200 if n <= 5 else 429))

sent = []   # (name, expected, received, response JSON or None)


def send(name, path, kwargs, expected):
    r = requests.post(BASE + path, timeout=60, **kwargs)
    try:
        body = r.json()
    except ValueError:
        body = None
    sent.append((name, expected, r.status_code, body))
    print(f"  {name:22} expected {expected}  got {r.status_code}")
    return body


before = len(audit.read_entries())
print(f"trial {trial}")
for name, path, kwargs, expected in PLAN:
    send(name, path, kwargs, expected)

# ─── Requests 21-24: appeals, against the first normal decision ──────────────
first_id = sent[0][3]["content_id"] if sent[0][2] == 200 else "missing"
owner = f"m5_c1_t{trial}_n1"
other = f"m5_c1_t{trial}_n2"
appeal = {"content_id": first_id, "creator_id": owner,
          "reasoning": "I wrote this myself.", "attestation": True}

send("appeal: valid",         "/appeal", {"json": appeal}, 200)
send("appeal: attestation",   "/appeal", {"json": {**appeal, "attestation": False}}, 400)
send("appeal: not the owner", "/appeal", {"json": {**appeal, "creator_id": other}}, 403)
send("appeal: no such id",    "/appeal",
     {"json": {**appeal, "content_id": "00000000-0000-0000-0000-000000000000"}}, 404)

# ─── The checks from criteria.md ─────────────────────────────────────────────
new = audit.read_entries()[before:]
received = [s[2] for s in sent]
decisions = [e for e in new if e.get("status") == "decided"]
repeats = [e for e in decisions if e.get("creator_id") == f"m5_c1_t{trial}_repeat"]
DECISION_FIELDS = ["stage_ms", "model_was_loaded", "text_chars", "text_words", "text_sha256"]


def strings(obj):
    """Every string inside a log record, however deeply nested."""
    if isinstance(obj, str):
        yield obj
    elif isinstance(obj, dict):
        for v in obj.values():
            yield from strings(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from strings(v)


# The 8 texts the "no submitted text" check covers: at least 40 characters
# after trimming. The whitespace-only and 3-word texts are under 40.
submitted = NORMAL + [REPEAT, TOO_LONG]
searched = [t.strip()[:40] for t in submitted if len(t.strip()) >= 40]
all_values = [s for e in audit.read_entries() for s in strings(e)]
matches = {probe: sum(probe in v for v in all_values) for probe in searched}

checks = {
    "exactly_24_new_lines": len(new) == 24,
    "received_as_planned": received == [s[1] for s in sent],
    "status_matches_log_24_of_24": len(new) == 24 and all(
        e.get("http_status") == code for e, code in zip(new, received)),
    "every_line_endpoint_and_duration": all(
        "endpoint" in e and isinstance(e.get("duration_ms"), (int, float)) and e["duration_ms"] >= 0
        for e in new),
    "eleven_complete_decisions": len(decisions) == 11 and all(
        all(f in d and d[f] is not None for f in DECISION_FIELDS) for d in decisions),
    "exactly_one_cold": sum(d.get("model_was_loaded") is False for d in decisions) == 1,
    "repeat_fingerprints_identical": len(repeats) == 5
                                     and len({d["text_sha256"] for d in repeats}) == 1,
    "eight_texts_zero_matches": len(searched) == 8 and sum(matches.values()) == 0,
}
met = all(checks.values())

result = {
    "criterion": 1,
    "trial": trial,
    "new_lines": len(new),
    "requests": [{"name": n, "expected": e, "received": r} for n, e, r, _ in sent],
    "text_matches": matches,
    "checks": checks,
    "met": met,
    "new_records": new,
}
out.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

print(f"  new log lines: {len(new)}   decisions: {len(decisions)}   texts searched: {len(searched)}")
for name, ok in checks.items():
    print(f"  {'PASS' if ok else 'FAIL'}  {name}")
print(f"  -> {'MET' if met else 'MISSED'} this trial   (saved to {out})")