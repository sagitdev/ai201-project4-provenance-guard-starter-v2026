# Acceptance criteria — Provenance Guard

Five criteria that say what "working" means for this service, written in unit 7
**before** you built it.

**All five are yours.** None are given.

An acceptance criterion names a number or something plainly observable. *"The
detector is accurate"* is an opinion — and perfect AI detection isn't possible
anyway, so it's an opinion about something nobody can deliver. *"Of 10 pieces I
wrote myself, at most 1 is labelled high-confidence AI"* is a criterion.

Under each, write a sentence or two on **why that target**. *"I allow at most 1
false positive in 10 because on a writing site a wrong accusation costs more
than a missed detection"* is a real answer.

> Missing your own targets next unit costs you nothing. Setting a target so
> easy you can't miss it does.

---

## Pick numbers you can defend

**Cover at least three of these five areas.** They're prompts, not a form.

| Area | A question it could answer |
|---|---|
| False positives | How often may a human's writing get called AI? |
| Score spread | How far apart should clearly-AI and clearly-human text score? |
| Label coverage | Is every one of your three labels actually reachable? |
| The appeal path | Does an appeal always change status and always get recorded? |
| Bad input | What happens when `text` is missing, empty, or enormous? |

Two things worth knowing before you pick numbers:

- **The expensive mistake is one-sided.** Missing some AI text costs the site a
  little. Accusing a real writer costs that person a lot. A criterion that
  treats both errors as equally bad is describing a system nobody would ship.
- **Unit 8 tests across three trials, and the target has to hold across all
  three.** Your first signal runs a model, so identical input can score
  differently twice. A target of "at most 1 in 10" against trials of 2, 1, 2 is
  a **miss**.

---
## 1. My own writing is not called AI

I prepare 10 pieces I wrote myself, each at least 3 sentences and 50 words.
Seven are in my normal style. Three are deliberately hard cases, one for each
risk:

- **plain** — everyday words, an average of 10 words or fewer per sentence
  (like a primary-school essay);
- **formulaic** — a fixed format: step-by-step instructions or a lab report;
- **uniform formal** — an academic-style paragraph whose sentences are all of
  similar length.

**Target:** 0 of the 10 are labeled high-confidence AI, and at most 3 are
labeled unsure, in every one of three trials. That means at least 7 are
labeled high-confidence human, so meeting this criterion also shows the human
label is reachable.

**Why this target:**

- A writer has no way to prove they didn't use AI (milestone1.md, section 3).
  Calling a real person's work AI is the most expensive mistake this system
  can make, so it isn't allowed even once.
- The hard cases are there because they are exactly what the signals find
  easiest to mistake for AI: GPT-2 predicts plain writing easily, and even,
  repetitive text looks machine-like to the style signal. The 12-year-old's
  piece from milestone 1 currently scores 0.695, already over the 0.65 line,
  so this target is genuinely hard. One piece per risk also means that when
  something fails in unit 8, I can tell which signal it was.
- Unsure is capped at 3, the number of hard cases. Under the rule "when the
  two signals disagree, the answer is unsure", a hard case landing in unsure
  is the system protecting that writer, not failing. But the 7 pieces with a
  clear personal style should all be read as human.
  - Below 3, the only way to pass would be raising the AI threshold, which
    lets AI through.
  - Above 3 — say 5 — a real writer would have half their work carrying
    "we're not sure you wrote this". Unsure isn't an accusation, but it is
    still doubt, and with half their work under it they'd feel doubted as a
    whole. It would also let ordinary pieces land in unsure, and a looser cap
    makes it easy to pass just by widening the unsure band.

---

## 2. Clearly-AI and clearly-human text score far apart

Two groups of 5:

- **AI:** 5 essays written by a chatbot from ordinary prompts with no
  instruction to "sound human". I record which chatbot and the exact prompt
  for each (e.g. *"Write a 200-word essay about friendship."*).
- **Mine:** 5 of the 7 normal-style pieces from criterion 1, chosen in advance
  and fixed in `scenarios.py`.

**Target:** the AI group's average `confidence` is at least **0.30** higher
than my group's, in every one of three trials.

**Why this target:**

- Under the current thresholds, 0.30 is exactly the width of the unsure band
  (0.35–0.65). If the two averages are closer than that, they can't fall on
  opposite sides of it, and the labels are only guessing.
- A big enough gap doesn't guarantee they *do* fall on opposite sides — that's
  what criterion 1 (my writing stays out of AI) and criterion 3 (most AI text
  goes over the AI threshold) check. This criterion measures one thing on its
  own: whether the signals can separate the two groups. So if criterion 2
  passes but criterion 3 fails, the problem is the thresholds; if criterion 2
  fails too, the problem is the signals.
- Averaging 5 pieces smooths out the small trial-to-trial wobble in the model
  signal.

---

## 3. All three labels appear, and ordinary AI text gets caught

- Of the 5 AI essays from criterion 2, **at least 3** are labeled
  high-confidence AI.
- 3 **mixed** pieces — an AI writes a first draft, then I rewrite every other
  sentence by hand: **at least 2** are labeled unsure.
- Both hold in every one of three trials. The high-confidence human label is
  covered by criterion 1.

**Why this target:**

- Missing some AI text costs less than accusing a person, so 2 of 5 are
  allowed to slip through. But a detector that never says "AI" is just a
  rubber stamp.
- `config.py` warns that with a weighted average and a style signal stuck at
  0.5, some labels can't be reached at all. This criterion catches that.
- Mixed writing is what the unsure label exists for. If these pieces always
  land at one end, the middle label is decoration.

---

## 4. A valid appeal always changes status and is recorded; an invalid one changes nothing

- **5 valid appeals** (a real `content_id`, the matching `creator_id`, a
  non-empty `reasoning`, `attestation: true`): 5 of 5 return `200` with
  `status: "under_review"`. In `GET /log`, each appeal adds exactly one new
  `under_review` entry carrying the reasoning, and the original `decided`
  entry is unchanged.
- **3 invalid appeals** — wrong `creator_id`, `attestation: false`,
  nonexistent `content_id` — return `403`, `400` and `404` respectively, and
  add no `under_review` entry to the log.
- Tested by hand with `curl` (`run_eval.py` only sends to `/submit`), three
  times.

**Why this target:**

- **Why 5 of 5 and not 4 of 5:** as the milestone 1 trace admits, a writer
  can't prove they didn't use AI, so an appeal is a wrongly flagged person's
  only way out. Detection is allowed to make mistakes (criterion 3 lets some
  AI through), but an appeal only files a record — it involves no judgement,
  so there's no reason for it ever to fail. 4 of 5 would mean one in five
  wrongly flagged people has their only way out blocked, without even knowing
  it.
- **Why an invalid appeal must change nothing:** the system reads an item's
  current status from its latest log entry. If an invalid appeal — someone
  else's `creator_id`, no attestation, a `content_id` that doesn't exist —
  could still write an `under_review` entry, anyone could send other people's
  work to review at will, or bury reviewers under fake appeals. Real appeals
  from wrongly flagged writers would get lost, and in unit 8 I couldn't tell
  real appeals from fake ones when reading the log.

---

## 5. Bad input gets a clear 400 and never crashes the service

Nine bad requests to `/submit`: no `text`; `text: ""`; only whitespace;
`text: null`; `text: 123`; fewer than 5 words (`"Hi"`); 50,001 characters; a
JSON list instead of an object; no `creator_id`.

**Target**, in every one of three trials:

- 9 of 9 return `400` with both an `error` code and a `message`;
- 0 return `500`;
- 9 of 9 are logged as `rejected`;
- the service is freshly restarted before each trial, and after all nine,
  `GET /health` still shows `detector_loaded: false` — no bad request ever
  reached the model.

**Why this target:**

- A crash on bad input has no grey area. No threshold makes a `500`
  acceptable, so anything less than 9 of 9 is a bug.
- The `/health` check proves every validation, including the length limit and
  the 5-word minimum, runs *before* the model. If an enormous text reached
  GPT-2 first, a script sending them over and over could tie up the whole
  service.
- I first wrote this as "the 50,001-character request is rejected within 1
  second". That doesn't prove the order: only the first model call is slow;
  once the model is loaded a run takes a second or two, and it only reads the
  first 400 tokens however long the text is. `detector_loaded` is a yes/no
  fact that doesn't depend on how fast the laptop is.
- Writing it this way showed the "too short" case relied on the detector
  raising an error, which means loading the model first. So `/submit` rejects
  text under 5 words itself, before the model is ever called.


---

<!-- ─────────────────────────────────────────────────────────────────────────
     UNIT 8 — read this before you change anything above.

     If a criterion turns out to be BROKEN rather than merely unmet, you can
     revise it, and that earns credit. But never delete or edit the original
     line. Add the revision underneath, like this:

         ## 2. Uncertain cases land in the unsure band

         The system handles uncertain cases well.

         **Why this target:** ...

         > **Revised in unit 8:** Text I judged borderline scores between
         > 0.4 and 0.6 in at least 4 of 5 cases.
         >
         > **Why revised:** "well" gave me nothing to check. I couldn't
         > reach a verdict from it at all.

     That's a revision because the criterion couldn't be MEASURED.

     Lowering a target because you missed it is not a revision, and it costs
     you the point:

         ✗ "At most 1 of 10 of my own pieces flagged as AI" → "at most 3
            of 10", because 1 of 10 turned out to be hard.

     A number you missed stays where it is, gets diagnosed, and gets a fix
     attempted. That's where the points are.
     ───────────────────────────────────────────────────────────────────────── -->

---

# Capstone criteria

Five criteria for the capstone extension (timing and logging, Shape A),
written before any Milestone 5 run. The five above are units 7–8 and stay as
they were. I wrote these in Chinese; Claude translated them into English
without adding or removing anything.

Criteria 1, 2, 3 and 5 are about the extension. Criterion 2 is the bad path.

---

## 1. Every request leaves exactly one complete timing record, and no submitted text

**Test:**

- Before each trial, stop the service completely, confirm the port is free
  with `lsof -nP -iTCP:5000 -sTCP:LISTEN` (no output), and start it again with
  the command in RUNNING.md. That way the first submission is always a cold
  start, and the rate-limit counts start at zero.
- A script sends 24 requests one at a time, in a fixed order, and records each
  status code:

| Requests | Expected |
|---|---|
| 6 normal submissions, each with its own `creator_id` (the first is a cold start) | 6 × 200 |
| 7 bad submissions: not JSON, a JSON list, no `creator_id`, no `text`, whitespace only, 3 words, 50,001 characters | 7 × 400 |
| The same `creator_id` submitting the same text 7 times | 5 × 200, then 2 × 429 |
| 4 appeals: a valid one, `attestation` false, someone else's `creator_id`, a `content_id` that doesn't exist | 200, 400, 403, 404 |

- What each request counts against for rate limiting, so that 429 appears only
  where expected:
  - not JSON, a JSON list and no `creator_id` have no `creator_id` to count
    against, so they count against the IP: 3 in all;
  - the other 4 bad submissions share one `creator_id` (`m5_bad`): 4 in all;
  - the 6 normal submissions each use their own `creator_id`: 1 each;
  - the 7 repeats share one `creator_id`, and the 6th and 7th return 429 —
    that's the expected result;
  - `/appeal` isn't rate limited.

  No counter goes over 5 a minute except the repeat group, which goes over on
  purpose.

**Target** (every one of the three trials must meet all of these):

- The log grows by exactly **24** lines.
- The `http_status` on line n equals the n-th status code the script
  received: **24/24**.
- Every line has `endpoint`, and `duration_ms` is a number ≥ 0.
- All 11 decision records have `stage_ms` (model, style, combined),
  `model_was_loaded`, `text_chars`, `text_words` and `text_sha256`, and
  **exactly 1** of them has `model_was_loaded: false`.
- The 5 decisions from the repeated submission have identical `text_sha256`.
- Take every submitted text that is **at least 40 characters** after trimming
  leading and trailing spaces — 8 texts: the 7 different texts that were
  decided (6 normal + 1 repeated) and the 50,001-character one. Search the
  whole log for the first 40 characters of each: **0** matches.

**What the text check covers:**

- The whitespace-only and 3-word texts are left out: the first has no content,
  and the second is so short that searching for it could match ordinary words
  elsewhere in the log.
- An appeal's `reasoning` is written to the log **by design**, because the
  person reviewing the appeal needs to read it, so it's outside this check. The
  appeal reason in the test is a fixed sentence, "I wrote this myself.", not a
  writer's work.

**Why this target:**

- **Exactly 24:** the point of this extension is that a failed request leaves a
  record instead of nothing. One line short, and it looks as if that request
  never arrived — and you can't even count how many are missing. One line too
  many is wrong too: `capstone_cost.py` adds the times up, so a duplicate record
  would overstate the cost. Writing the log uses no model and has no
  randomness, so anything other than 24/24 is a bug, not variation.
- **The status codes must match:** status codes are how the log tells requests
  apart later. If a 429 were logged as 200, a flood would look like seven
  ordinary writers.
- **Exactly one cold start:** `capstone_cost.py` uses `model_was_loaded` to
  separate cold starts (8.9 s) from warm requests (0.17 s). One wrong flag and
  the cost per run is off by several seconds. That's also why every trial
  restarts the service: without a restart, trials 2 and 3 would have no cold
  start to check.
- **Zero copies of the text:** `audit.jsonl` is committed to a public GitHub
  repository. Once a writer's unpublished draft is in it, deleting the line
  later doesn't help — it's still in the git history and can't be taken back.
  So the allowance is 0. And the fingerprint must give the same value for the
  same text, or there's no way to notice the same text being submitted again.

---

## 2. A crash returns a JSON 500, leaves a record, and the service stays usable

**Test:** the real server can't be made to crash on demand without adding a
"crash switch" to production code, so this runs in a test process
(`app.test_client()`, with `config.AUDIT_LOG` pointed at a temporary file), the
same way as in M2. `unittest.mock.patch` makes four failures, one at a time:

- a. `detector.model_signal` raises
- b. `stylometry.style_signal` raises
- c. `scoring.combine_signals` raises
- d. the log can't be written (`audit._append` raises `OSError`, standing in
  for a full disk)

**Target** (every one of the three trials must meet all of these):

- **4/4** return 500 with a JSON body that has `error` and `message`, and
  **no** `content_id`.
- a, b and c each leave **exactly one** `event: "error"` record with
  `error_type`, `http_status: 500` and `duration_ms`.
- d can't write to the log, so instead: the test captures `app.logger`'s
  output with `assertLogs`, and that output contains `OSError`.
- After each failure, a normal `/submit` in the same process returns 200.

**Why this target:**

- **4/4:** there's no randomness here.
- **It must be JSON:** every caller of this service reads the reply with
  `.json()`. An HTML error page makes the caller fail too, and the writer sees a
  broken page instead of "please try again".
- **d must not return a `content_id`:** if the decision can't be written,
  there's no `decided` line, so any later appeal against that `content_id`
  gets a 404. If the label had said "written by AI", that would accuse the
  writer and then close off their only way out. That's worse than a plain
  error.
- **The service must stay usable:** there's only one worker, and no second
  process to take over.
- **Why d checks the logger's output:** the log file is the only record, so
  when it can't be written, what `app.logger` prints is the only place the
  problem can be found.

---

## 3. A cold start uses at most half of gunicorn's 30-second timeout

**Test:**

- Stop the service completely (`lsof` prints nothing).
- Run `sudo purge` to empty macOS's file cache (it asks for a password), so
  every trial really reads the 525 MB of model files from disk.
- Start the service with the RUNNING.md command, wait until `/ping` answers,
  and only then send the first `/submit`. That way the measurement is the
  model loading plus the first inference, not gunicorn's own start-up.
- The first `/submit` uses the **first text of criterion 4's 1,000-word group**
  (starting from #1; 1,248 tokens, so the model reads a full 400).
- Repeat three times, doing every step above each time.

**Target:** all three return 200, the record has `model_was_loaded: false`,
and `duration_ms` ≤ **15,000**.

**Why this target:**

- **30 seconds is a hard wall:** past it, gunicorn kills the worker. The writer
  gets a dropped connection, and there's no line in the log because the worker
  died before it could write one. The new worker hasn't loaded GPT-2, so the
  next request is a cold start again and can die the same way. The service
  could keep timing out with not a single line in the log.
- **Why half:** on the same laptop with nothing changed, cold starts already
  ranged from 8.0 to 13.8 seconds — a factor of 1.7. A 2× margin is the
  smallest that absorbs one more swing of that size (another machine, a busy
  laptop) without reaching 30 seconds. A 25-second target would leave only
  1.2×, less than the swing I've already seen.
- **Why not stricter,** say 10 seconds: a cold start affects one writer per
  restart, and everyday waiting is criterion 4's job. This one is about the
  first request not failing.
- **Why a full 400-token text:** it makes the first inference the heaviest the
  model step can be. It's also the same text criterion 4 uses, so the two
  results can be compared.
- **Why empty the cache:** the time this wall is most likely to be hit is the
  first start after the computer restarts, when the model files aren't in the
  cache. Without emptying it, trials 2 and 3 would measure a "cached cold
  start", which is easier than the real case, and this would become the easy
  version of the criterion. The 8.0–13.8 second spread may already mix cached
  and disk reads; with the cache emptied, all three trials measure the same
  worst case.
- This one really can miss: 13.8 seconds is already close to 15. If it does,
  the fix is to load the model at start-up instead of on the first request.

---

## 4. A warm request answers within 1 second, even for the longest valid text

**Test:** send one warm-up request, then 12 texts in four length groups of
three. Each text uses its own `creator_id`. Three trials.

**Where the texts come from:** all 18 source texts are in `scenarios.py`, in
the file's order: #1–#10, AI1–AI5, M1–M3. Joined texts have one space between
pieces.

| Group | Text 1 | Text 2 | Text 3 |
|---|---|---|---|
| **~100 words** | AI2 (101 words, 116 tokens) | AI3 (101 words, 116 tokens) | M3 (100 words, 114 tokens) |
| **~300 words** | AI5 + #7 + #6 (285 words, 365 tokens) | M1 + #8 + #5 (285 words, 353 tokens) | AI4 + AI1 + M2 (295 words, 348 tokens) |
| **~1,000 words** | starting from #1 | starting from AI1 | starting from M1 |
| **49,000 characters** | starting from #1 | starting from AI1 | starting from M1 |

- **1,000-word group:** start from the named text, join texts in file order
  (after M3, wrap back to #1), split on whitespace and keep the first
  **1,000** words. The three are 1,248, 1,206 and 1,223 tokens.
- **49,000-character group:** join whole texts in the same looping order until
  past 49,000 characters, then cut at the last space within the first 49,000.
  The three are 48,999, 48,991 and 48,993 characters, about 10,700 tokens.

Word, character and token counts were measured with GPT-2's tokenizer only —
no model run, no log written.

What each group tests:

- ~100 words: about 115 tokens;
- ~300 words: about 350 tokens, still under the cut-off;
- ~1,000 words: over 400, so the model reads only the first 400;
- 49,000 characters: the tokenizer first reads all ~10,700 tokens, then cuts
  to 400.

**Target** (every one of the three trials must meet both; MET only if both
hold):

- **A.** All 12 texts have a **client time** ≤ **1,000 ms**. Client time is
  from the script sending the request to receiving the reply. This looks at
  the slowest text, not the average.
- **B.** For every one of the 12: client time − `duration_ms` ≤ **50 ms**.

**Why this target:**

- **1 second:** past about a second, a writer starts to wonder whether
  anything happened, and clicks again. Every click uses one of the 5 a minute,
  so a slow reply can push a writer straight into a 429.
- **The slowest, not the average:** the person who submitted the long piece
  doesn't experience the average.
- **Why these lengths:** M3 only tested 59–110 words. The tokenizer reads the
  whole text before cutting it to 400 tokens, so "the longest valid input" has
  never been tested.
- **Why not looser:** the warm path makes no network or API call. Several
  seconds would mean something is wrong.
- **Why A uses client time:** that's what the writer waits for. `duration_ms`
  is for diagnosing which stage the time went to.
- **Why B as well:** once it's really running there's no client stopwatch,
  only the log. For the log to tell how long a writer waited, its error has to
  be under 5% of the budget, which is 50 ms. Otherwise a record saying 960 ms
  could mean a writer waited over a second. B checks whether the extension
  itself measures correctly.

---

## 5. After a year of log, an appeal still answers within 1 second

**Test:**

- Copy the log to a temporary location and pad it to **46,000** lines by
  copying lines 415–443 of the real log over and over, giving each decision a
  new `content_id`. That keeps the line lengths, and the mix of decisions,
  rejections and appeals, the same as the real log. Reading a file takes time
  by bytes, not by lines.
- In a test process, point `config.AUDIT_LOG` at that copy and send 5 valid
  appeals.
- Three trials.

**Target:** every trial is **5/5** returning 200, and every appeal's
`duration_ms` ≤ **1,000**.

**Why this target:**

- **1 second, the same as criterion 4:** an appeal shouldn't be slower than the
  accusation.
- **It belongs to this extension:** `audit.entries_for` reads the whole log on
  every appeal. The 5.5 ms in M3 was measured on 443 lines and says nothing
  about line 46,000. Every line this extension adds makes every future appeal
  slower.
- **Which decision an appeal targets doesn't matter:** `entries_for` reads and
  parses the whole file whichever one it's looking for. So the 5 appeals are 5
  samples of the same operation, not a comparison of positions.
- **Why a year:** nothing in the design ever trims the log, so its size depends
  only on how long the service has run. A year is the shortest time I'd call
  "in production". At the README's 100 submissions a day, a year is
  100 × 365 = 36,500 decisions. In the mix of lines 415–443 (23 decisions in
  every 29 lines), that's 36,500 × 29 / 23 ≈ 46,000 lines.
