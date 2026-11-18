#!/usr/bin/env python3
"""
Capstone M3 — one real session against the running service.

Start the service first, in another terminal (see RUNNING.md):

    gunicorn app:app --bind 127.0.0.1:5000 --workers 1

Then:

    python capstone_session.py

Every request below is written to logs/audit.jsonl by the service itself.
This script only sends requests and prints what came back.
"""

import sys
import time

import requests

from scenarios import AI_ESSAYS, MIXED, MY_WRITING

BASE = "http://127.0.0.1:5000"


def send(name, path, **kwargs):
    """Send one POST, print one line, return the response."""
    t = time.perf_counter()
    r = requests.post(BASE + path, timeout=60, **kwargs)
    client_ms = round((time.perf_counter() - t) * 1000, 1)
    print(f"{name:32} {r.status_code}  client {client_ms:>8} ms")
    return r


# 1. Is the service up?
try:
    requests.post(BASE + "/ping", json={"message": "hello"}, timeout=5)
except requests.ConnectionError:
    sys.exit("The service isn't running. Start gunicorn first (see RUNNING.md).")

# 2. Real submissions: every Unit 7-8 test text, one creator_id each.
texts = {**MY_WRITING, **AI_ESSAYS, **MIXED}
first_id = None
for i, (label, text) in enumerate(texts.items(), start=1):
    r = send(label, "/submit", json={"creator_id": f"m3_run_{i:02d}", "text": text})
    if first_id is None and r.status_code == 200:
        first_id = r.json()["content_id"]

# 3. Requests that should be refused.
send("bad JSON", "/submit", data="not json", headers={"Content-Type": "application/json"})
send("missing text", "/submit", json={"creator_id": "m3_bad"})
send("too short", "/submit", json={"creator_id": "m3_bad", "text": "too short"})

# 4. Rate limit: one creator_id, more than 5 in a minute.
flood_text = MY_WRITING["#9 sorry"]
for n in range(1, 8):
    send(f"flood {n}", "/submit", json={"creator_id": "m3_flood", "text": flood_text})

# 5. One appeal, against the first decision.
if first_id:
    send("appeal", "/appeal", json={
        "content_id": first_id,
        "creator_id": "m3_run_01",
        "reasoning": "I wrote this myself.",
        "attestation": True,
    })