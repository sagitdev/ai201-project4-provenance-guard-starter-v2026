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
