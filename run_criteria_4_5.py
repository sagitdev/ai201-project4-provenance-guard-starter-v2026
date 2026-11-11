#!/usr/bin/env python3
"""
One trial of criteria 4 (appeals) and 5 (bad input).  <- UNIT 8, MILESTONE 3

run_eval.py only sends to /submit, and a "bodies" scenario can only hold a
dict, so these two criteria get their own runner. It is a test tool only. It
changes nothing in the service.

    # 1. restart app.py  (criterion 5 needs a fresh start: detector not loaded)
    # 2. then:
    python run_criteria_4_5.py --trial 1 --label before
    # repeat for --trial 2 and --trial 3, restarting app.py before each

Order inside a trial matters: criterion 5 runs FIRST, because criterion 4
submits real text, and that loads the model.

It records counts against each target and saves every raw response to
results/. It does not write MET or MISSED. That call is made in M4.
"""

import argparse
import datetime as dt
import json
import sys

import requests

import config

URL = f"http://{config.HOST}:{config.PORT}"


def log_entries():
    return requests.get(f"{URL}/log", timeout=10).json()["entries"]


def health():
    return requests.get(f"{URL}/health", timeout=10).json()


def post(path, *, json_body=None, raw=None):
    """Send one request. Returns status, parsed body (or the raw text if it isn't JSON)."""
    if raw is not None:
        r = requests.post(f"{URL}{path}", data=raw,
                          headers={"Content-Type": "application/json"}, timeout=90)
    else:
        r = requests.post(f"{URL}{path}", json=json_body, timeout=90)
    try:
        body = r.json()
    except ValueError:
        body = {"_not_json": r.text[:200]}
    return r.status_code, body


# ─── Criterion 5 ─────────────────────────────────────────────────────────────

def criterion_5(trial):
    tag = f"c5_t{trial}"
    cases = [
        ("no text field", {"creator_id": f"{tag}_notext"}),
        ("text is empty string", {"text": "", "creator_id": f"{tag}_empty"}),
        ("text is only whitespace", {"text": "   \n\t  ", "creator_id": f"{tag}_space"}),
        ("text is null", {"text": None, "creator_id": f"{tag}_null"}),
        ("text is a number", {"text": 123, "creator_id": f"{tag}_number"}),
        ("fewer than 5 words", {"text": "Hi", "creator_id": f"{tag}_short"}),
        ("50,001 characters", {"text": "a" * 50_001, "creator_id": f"{tag}_huge"}),
        ("body is a JSON list", "LIST"),
        ("no creator_id", {"text": "This piece has text but nobody signed it."}),
    ]
    before_health = health()
    before_count = len(log_entries())

    results = []
    for name, body in cases:
        if body == "LIST":
            status, resp = post("/submit", raw=json.dumps(["text", "creator_id"]))
        else:
            status, resp = post("/submit", json_body=body)
        results.append({"case": name, "status": status, "response": resp})

    new_entries = log_entries()[before_count:]
    after_health = health()

    summary = {
        "fresh_start (detector_loaded false before)": before_health["detector_loaded"] is False,
        "returned 400": sum(r["status"] == 400 for r in results),
        "400 with both error and message": sum(
            r["status"] == 400 and "error" in r["response"] and "message" in r["response"]
            for r in results),
        "returned 500": sum(r["status"] >= 500 for r in results),
        "returned 429": sum(r["status"] == 429 for r in results),
        "new log entries": len(new_entries),
        "new entries with status rejected": sum(e.get("status") == "rejected" for e in new_entries),
        "detector_loaded after": after_health["detector_loaded"],
    }
    return {"target": "9/9 are 400 with error+message, 0 are 500, 9/9 logged rejected, "
                      "detector_loaded false after",
            "summary": summary, "requests": results, "new_log_entries": new_entries}


# ─── Criterion 4 ─────────────────────────────────────────────────────────────

def criterion_4(trial):
    tag = f"c4_t{trial}"

    # Five submissions to appeal against, each from its own creator.
    submitted = []
    for i in range(1, 6):
        creator = f"{tag}_writer{i}"
        text = (f"This is test submission number {i} for the appeal criterion. "
                f"I wrote it so that trial {trial} has a real content id to appeal against.")
        status, resp = post("/submit", json_body={"text": text, "creator_id": creator})
        submitted.append({"creator_id": creator, "status": status, "content_id": resp.get("content_id")})

    entries_before = log_entries()
    originals_before = {
        s["content_id"]: [e for e in entries_before
                          if e.get("content_id") == s["content_id"] and e.get("status") == "decided"]
        for s in submitted
    }
    count_before = len(entries_before)

    # Five valid appeals.
    valid = []
    for s in submitted:
        reasoning = f"I wrote this myself ({s['creator_id']}, trial {trial})."
        status, resp = post("/appeal", json_body={
            "content_id": s["content_id"], "creator_id": s["creator_id"],
            "reasoning": reasoning, "attestation": True})
        valid.append({"content_id": s["content_id"], "reasoning": reasoning,
                      "status": status, "response": resp})

    after_valid = log_entries()
    new_after_valid = after_valid[count_before:]

    def under_review_for(cid, entries):
        return [e for e in entries if e.get("content_id") == cid and e.get("status") == "under_review"]

    per_appeal = []
    for v in valid:
        added = under_review_for(v["content_id"], new_after_valid)
        originals_now = [e for e in after_valid
                         if e.get("content_id") == v["content_id"] and e.get("status") == "decided"]
        per_appeal.append({
            "content_id": v["content_id"],
            "200 and under_review": v["status"] == 200 and v["response"].get("status") == "under_review",
            "exactly one new under_review entry": len(added) == 1,
            "entry carries the reasoning": len(added) == 1 and added[0].get("reasoning") == v["reasoning"],
            "original decided entry unchanged": originals_now == originals_before[v["content_id"]],
        })

    # Three invalid appeals, each against a real submission except the last.
    target = submitted[0]
    invalid_cases = [
        ("wrong creator_id", 403, {"content_id": target["content_id"], "creator_id": f"{tag}_someone_else",
                                   "reasoning": "Not mine to appeal.", "attestation": True}),
        ("attestation false", 400, {"content_id": submitted[1]["content_id"],
                                    "creator_id": submitted[1]["creator_id"],
                                    "reasoning": "Forgot to tick the box.", "attestation": False}),
        ("nonexistent content_id", 404, {"content_id": f"does-not-exist-{tag}",
                                         "creator_id": f"{tag}_writer1",
                                         "reasoning": "This id was never issued.", "attestation": True}),
    ]
    count_before_invalid = len(after_valid)
    invalid = []
    for name, expected, body in invalid_cases:
        status, resp = post("/appeal", json_body=body)
        invalid.append({"case": name, "expected": expected, "status": status, "response": resp})
    new_after_invalid = log_entries()[count_before_invalid:]

    summary = {
        "submissions that returned 200": sum(s["status"] == 200 for s in submitted),
        "valid appeals: 200 + under_review": sum(p["200 and under_review"] for p in per_appeal),
        "valid appeals: exactly one new under_review entry": sum(p["exactly one new under_review entry"] for p in per_appeal),
        "valid appeals: entry carries the reasoning": sum(p["entry carries the reasoning"] for p in per_appeal),
        "valid appeals: original decided entry unchanged": sum(p["original decided entry unchanged"] for p in per_appeal),
        "invalid appeals: got the expected status": sum(i["status"] == i["expected"] for i in invalid),
        "invalid appeals: under_review entries added": sum(
            e.get("status") == "under_review" for e in new_after_invalid),
    }
    return {"target": "5/5 valid appeals pass all four checks; 3 invalid return 403/400/404 "
                      "and add 0 under_review entries",
            "summary": summary, "submitted": submitted, "valid_appeals": valid,
            "per_appeal_checks": per_appeal, "invalid_appeals": invalid,
            "log_entries_added_by_invalid": new_after_invalid}


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--trial", type=int, required=True)
    parser.add_argument("--label", default="")
    args = parser.parse_args()

    try:
        h = health()
    except Exception:  # noqa: BLE001
        sys.exit(f"Nothing answering at {URL}. Start it:  python app.py")
    if h["detector_loaded"]:
        print("!! detector is already loaded, so this isn't a fresh start. "
              "Criterion 5 needs a restart first. Running anyway; the result will show it.\n")

    c5 = criterion_5(args.trial)
    c4 = criterion_4(args.trial)

    stamp = dt.datetime.now().strftime("%Y-%m-%d_%H%M%S")
    label = f"_{args.label}" if args.label else ""
    out = config.RESULTS_DIR / f"criteria45{label}_trial{args.trial}_{stamp}.json"
    config.RESULTS_DIR.mkdir(exist_ok=True)
    out.write_text(json.dumps({"produced_by": "run_criteria_4_5.py::main",
                               "trial": args.trial, "label": args.label,
                               "criterion_5": c5, "criterion_4": c4},
                              indent=2, ensure_ascii=False), encoding="utf-8")

    for name, block in (("Criterion 5", c5), ("Criterion 4", c4)):
        print(f"\n{name} · trial {args.trial}\n  target: {block['target']}")
        for k, v in block["summary"].items():
            print(f"  {k}: {v}")
    print(f"\nWrote {out.relative_to(config.ROOT)}")


if __name__ == "__main__":
    main()
