# Milestone 1 — Trace a submission before building one

## 1. The path a submission takes

<!-- 6–7 steps. For each: what it passes through, and what that step ADDS. -->

1. **The request arrives.** `app.py::submit` receives a `POST /submit` and
   parses the JSON body with `request.get_json(silent=True)` into a Python dict.
   *Adds:* structured data — `text` and `creator_id` — instead of raw bytes.
   Invalid JSON comes back as `None`, not a crash.

2. **Validate the input and assign an identity.** Still in `submit`. The text is
   rejected with a `400` if the body isn't a JSON object, or `text` is missing,
   empty, too short to score (`detector.perplexity` raises `ValueError` under 3
   tokens), or longer than a maximum length. Every rejection is recorded with
   `audit.log_rejection`. Accepted text gets a unique `content_id` from
   `uuid.uuid4()`.
   *Adds:* a pass/reject decision, and an identity — the `content_id` is how the
   log entry and any later appeal find this piece again.

3. **Signal one — the model signal.** `detector.py::model_signal()` →
   `perplexity()` → `_load()` (GPT-2, loaded once and kept in memory). The
   tokenizer splits the text into tokens (truncated at 400), GPT-2 measures its
   perplexity, and a logistic curve squashes that onto 0–1.
   *Adds:* `model_score` (higher = more likely AI) — an answer to "how
   predictable is this text to a language model?"

4. **Signal two — the style signal.** `stylometry.py::style_signal()`. It
   doesn't understand the words; it measures the shape of the text — how evenly
   sentence lengths march, how much vocabulary repeats, how punctuation is used.
   *Adds:* `style_score` (higher = more likely AI) — a second opinion measured
   from a completely different angle than signal one.

5. **Combine the two scores.** `scoring.py::combine_signals(model_score,
   style_score)`, using the weights in `config.py`.
   *Adds:* `combined_score`, returned as `confidence` — two possibly
   conflicting opinions become one number. What happens when the signals
   disagree is decided here. (Exactly what `confidence` means is defined in the
   contract, section 4.)

6. **Turn the score into words.** `scoring.py::score_to_label(score)`, compared
   against `config.HUMAN_THRESHOLD` (0.35) and `config.AI_THRESHOLD` (0.65).
   *Adds:* `guess` (`ai` / `human` / `unsure`, for programs) and `label` (a
   full sentence, for the writer). A number like 0.62 means nothing to a
   reader; this step translates it into meaning.

7. **Record the decision, then answer the writer.** `audit.py::log_decision()`
   → `_append()` writes one line to `logs/audit.jsonl`, then `app.py` returns
   the response with `jsonify(...)`.
   *Adds:* a permanent, append-only record with all nine fields, including
   `timestamp` and `status: "decided"`. An appeal never edits this line — it
   appends a new `under_review` entry after it, so an item's current status is
   its latest entry. Unit 8's diagnosis depends on this record. The writer
   receives `content_id, guess, confidence, label, model_score, style_score`,
   and needs the `content_id` to appeal.

## 2. The two signals

### Signal one — `detector.py` (model signal)

- **What it measures:** How *predictable* the text is to a language model
  (GPT-2) — its perplexity, squashed onto 0–1 so that low perplexity means a
  high AI score.
- **Why it might differ between human and AI writing:** A language model
  writes by repeatedly picking a likely next word, so text a model produced
  tends to be text a model finds easy to predict. Human writing wanders more —
  odd word choices, abrupt turns, the specific rather than the typical.
- **What it can't see (blind spot):** Predictability is not authorship.
  - **False positives (a human called AI):** anyone who writes with common
    words, short sentences and a plain style scores about as machine-like as a
    machine:
    - people writing in a second language, sticking to words they're sure of;
    - younger writers;
    - people writing plainly on purpose — explanations, step-by-step
      instructions;
    - genres that are formulaic by nature — news briefs, lab reports, cover
      letters.

    These are exactly the writers with the least room to argue back. The
    problem is structural to the method, not a bug that can be fixed.
  - **Quoting famous text.** A poem that quotes a well-known passage (say, the
    opening of the Declaration of Independence) contains words GPT-2 saw
    countless times in training and can predict almost word for word. The
    perplexity collapses and the quote reads as AI.
  - **False negatives (AI slipping through):** rare words and ornate prose are
    hard to predict, so their perplexity is high and they read as human. Asking
    an AI to "use less common words", or swapping a few words for rare synonyms
    afterwards, is enough to lower the score.
  - **Other things it can't see:**
    - It only reads the first 400 tokens; anything after that is invisible.
    - On short text the reading is unstable, and under 3 tokens it raises an
      error.
    - GPT-2 is a 2019 model; newer AI systems don't necessarily write in the
      way GPT-2 finds predictable.
    - It's an English model; scores on Chinese or other languages mean
      nothing.

### Signal two — `stylometry.py` (style signal)

- **What it measures:** The *shape* of the text, without reading it —
  sentence length spread (standard deviation ÷ mean), type-token ratio (unique
  words ÷ total words), and punctuation density.
- **Why it might differ between human and AI writing:** "Most likely next
  word" produces even, mid-length sentences and a narrower vocabulary on
  average. Human writing is lumpier — a three-word sentence next to a
  forty-word one. In a test of four texts, an AI paragraph had a spread of
  0.09 while a vivid human paragraph had 0.88.
- **What it can't see (blind spot):** It doesn't understand the content. Any
  edit that changes the shape without changing the substance moves the score.
  - **False negatives (AI slipping through):** changing the shape is very
    cheap, so it's easy to exploit on purpose:
    - **Adding typos:** every misspelling counts as a "new word", so
      vocabulary variety goes up and the text looks more human.
    - **Scrambling sentence lengths:** split some sentences into short ones and
      merge others into long ones, and the spread jumps. In the test, chopping
      up the AI paragraph moved its spread from 0.09 to 0.89 without changing
      what it said.
    - **Inserting quotations, lists or dialogue**, or a few semicolons and
      dashes, changes the punctuation profile.
  - **False positives (a human called AI):** people who naturally write
    evenly get accused:
    - academic or official writing with even sentence lengths and regular
      punctuation;
    - student essays trained to keep "every sentence a moderate length";
    - technical documentation that has to repeat the same terms (low
      vocabulary variety). In the test, human-written machine instructions
      scored as AI-like as the AI paragraph on all three measures.
  - **Sensitive to length:** type-token ratio falls naturally as text gets
    longer, because common words repeat. So longer text drifts toward "AI"
    for reasons that have nothing to do with who wrote it.
  - **Helpless on short text:** with only one or two sentences there's no
    spread to measure, and whatever default value I choose decides the
    result.

## 3. Tracing a false positive

<!-- A real writer submits real work and the system calls it AI. -->

- **Who they are / what they wrote:** A 12-year-old (or a student still
  learning English) writes a short piece about their day, every word their
  own:

  > "I go to school every day. I like my teacher. She is very nice. After
  > school I play with my friends and then I do my homework."

- **What score they got:**
  - `model_score` = **0.89** (measured — common words are easy for GPT-2 to
    predict).
  - `style_score` = **0.5** (signal two is still a stub returning a neutral
    0.5; a real one would likely score this higher, since the sentences are
    short, even and use simple words).
  - combined = 0.5 × 0.89 + 0.5 × 0.5 = **0.695**.

  0.695 ≥ the AI threshold of 0.65, so they're labeled **AI**. Even with
  signal two completely neutral, signal one alone pushed them over the line.

- **What the label said to them:** If it says *"This text was generated by
  AI,"* they'd be confused and want to know why. A bare verdict gives them
  nothing to understand or answer. The label should explain which features made
  the system unsure (very common words, evenly sized sentences). But it should
  **not** say how to rewrite the text to pass, for two reasons:
  - it's an instruction manual for anyone using AI to slip through
    (transparency vs. being gamed);
  - it pushes a real writer to abandon their own natural style just to look
    human, punishing them for how they actually write.

- **What they can do about it:** Appeal through `POST /appeal`.
  - **Finding the `content_id`:** it should be shown right next to the text
    and label, or the appeal form should list their submissions so they can
    pick one. So the `/submit` response *must* return `content_id`, and the
    label should mention that they can appeal.
  - **Proving it's theirs:** the only options I could think of are a signed
    statement that no AI was used, or a screen recording of the writing
    process. Both are heavy burdens for a 12-year-old, and a recording raises
    privacy problems. **There is no good way to prove you didn't use AI.**
  - **After the appeal:** the status moves to `under_review` and the appeal is
    recorded. There's no automatic re-check, so a human reviewer has to look
    at it and decide — outside the scope of this unit.

- **What I'd change to protect them, and what it costs:**

  | Change | Effect on this writer | Cost |
  |---|---|---|
  | Raise the AI threshold (0.65 → 0.8) | 0.695 is no longer labeled AI | Ornate AI text slips through more easily |
  | Lower signal one's weight | They might pass | Signal two alone is unreliable, and cheap to fool by re-chopping sentences |
  | Widen the unsure band **and** word the unsure label so it isn't an accusation | They land in "unsure" and are never accused | More AI text gets "unsure" instead of "AI" |
  | **Disagreement rule:** when the two signals disagree, the result is "unsure"; only when both agree can a confident label be given | 0.89 vs. 0.5 disagree → "unsure" | Needs both signals to catch AI, so AI that fools either one gets through |

  Limit of the disagreement rule: if this writer's sentences are also even
  and signal two scores 0.8, both signals *agree* — wrongly. That's the
  blind-spot overlap from section 2, and why thresholds, label wording and the
  appeal path are still needed as further layers.

- **Design principles this trace leads to:**
  1. A "high-confidence AI" label should be hard to get, because a writer has
     no way to prove their innocence.
  2. When the two signals disagree, the answer is "unsure".
  3. Labels explain the reason but never how to get around it; the "unsure"
     label must not read like an accusation.
  4. The `content_id` is easy to find, and an appeal goes to a human
     reviewer.

## 4. Endpoint contracts

### POST /submit

- **Request fields:** both required.

  | Field | Type | Why required |
  |---|---|---|
  | `text` | string | nothing to judge without it |
  | `creator_id` | string | without it, the log and any appeal can't be tied to a person |

- **Response fields (success)** — `200`:

  | Field | Type | Values | Meaning |
  |---|---|---|---|
  | `content_id` | string | a uuid, e.g. `"3f2a9c1e-..."` | this submission's id; needed to appeal |
  | `guess` | string | exactly one of `"ai"`, `"human"`, `"unsure"` | the verdict, for programs |
  | `confidence` | float | 0.0 – 1.0 | **how AI-like the text is**: 0 = very human-like, 1 = very AI-like. It's the combined score, *not* "how sure the system is" |
  | `label` | string | one full sentence | the verdict, for the writer |
  | `model_score` | float | 0.0 – 1.0, higher = more AI-like | signal one |
  | `style_score` | float | 0.0 – 1.0, higher = more AI-like | signal two |

  Why `confidence` means AI-likeness: the brief says *0.51 and 0.95 must
  produce different labels*, which treats it as a position on the
  human-to-AI scale; and it runs the same direction as the two signal scores,
  so all three can be compared side by side. The cost is that a reader could
  take "confidence 0.05" as "the system has no idea" — so this definition is
  written here, once, for anyone building against it.

- **Response when input is bad** — always `400`, never a `500`, and always the
  same shape:

  ```json
  {"error": "text_too_short", "message": "Please submit at least a few sentences so we can read it properly."}
  ```

  `error` is a short fixed code for programs; `message` is one sentence for a
  person. Every rejection is also written to the log with
  `audit.log_rejection`, along with the `endpoint` that refused it. When
  `creator_id` is missing, not a string, or too long, the rejection logs it as
  `null` — never a placeholder string like `"unknown"`, which a real writer
  could choose as their id.

  | Input | `error` |
  |---|---|
  | body isn't JSON, or isn't a JSON object | `invalid_json` |
  | `creator_id` missing, empty, or not a string | `creator_id_missing` |
  | `creator_id` longer than **100 characters** | `creator_id_too_long` |
  | `text` missing or not a string | `text_missing` |
  | `text` empty or only whitespace | `text_empty` |
  | `text` longer than **50,000 characters** | `text_too_long` |
  | `text` under 5 words — checked in `/submit` before the model runs, so a bad request never loads it (criteria.md #5) | `text_too_short` |

  Why 50,000 characters (~9,000 words): a poem is about 50–300 words, a short
  piece 500–1,500, a long piece 2,000–10,000. The limit isn't about accuracy —
  it protects the service from a giant input, or a script sending them
  repeatedly — so it should let almost every real piece through. Counted in
  characters because `len(text)` is one line of code. Note: signal one only
  reads the first ~300 words anyway, so a long piece is judged by model on its
  opening.

  Why 100 characters for `creator_id`: the caller writes it, not the service,
  and it goes into every log entry — rejections included. Without a cap, a
  request with a one-megabyte `creator_id` and a two-word `text` would be
  rejected before the model runs, yet still add a megabyte to the log. 100
  characters fits a username, a UUID (36) and nearly every real email address.
  A too-long id is logged as `null`, not cut short, because a shortened id
  could match a different real writer's id.

### POST /appeal

- **Request fields:**
  - `content_id` (string, required)
  - `creator_id` (string, required) — must match the `creator_id` of the
    original submission, so nobody can appeal someone else's work, or flood
    it with malicious appeals.
    - Honest limit: `creator_id` is not authentication. Anyone who knows or
      guesses a writer's id can type it. Real protection needs login, which
      is outside this unit.
    - Same 100-character limit as `/submit`.
  - `reasoning` (string, required) — every appeal needs a reason; it's what a
    human reviewer reads.
    - At most **5,000 characters** (~800 words), measured after trimming
      spaces at the start and end. The whole reasoning is written to the log,
      so without a cap, repeated huge appeals would grow the log without
      limit. 5,000 is far more than an explanation needs.
  - `attestation` (boolean, **required, must be `true`**) — the writer ticks
    a box saying *"I confirm this is my own writing."* If it turns out
    otherwise, the site's own rules apply.
    - Missing or `false` → `400`, with a message such as *"Please confirm this
      is your own work to submit an appeal."*
    - Why a checkbox and not a signed statement with legal liability: a legal
      threat mostly scares off the honest writers who were wrongly flagged
      (often children or second-language writers), while someone who used AI
      will sign anyway. A minor's signature usually has no legal force, using
      AI usually isn't illegal (it breaks site rules, not laws), and the
      service can't verify who signed. The checkbox keeps the point — the
      writer leaves a statement on record — without the chilling effect.
- **Response fields (success)** — `200`. The appeal is recorded with
  `audit.log_appeal` (a new `under_review` entry appended after the original
  decision) and confirmed:

  ```json
  {"content_id": "3f2a9c1e-...", "status": "under_review", "message": "We've received your appeal. A person will review it."}
  ```

  The wording says *received*, not *successful* — "appeal successful" could
  be read as "you won", when nothing has been decided yet.

- **Response when something is wrong** — same `error` + `message` shape as
  `/submit`, and logged the same way. Format is checked first (`400`), the log
  only after (`404`, `403`), in this order:

  | Situation | Status | `error` |
  |---|---|---|
  | body isn't a JSON object | `400` | `invalid_json` |
  | `content_id` missing, empty, or not a string | `400` | `content_id_missing` |
  | `creator_id` missing, empty, or not a string | `400` | `creator_id_missing` |
  | `creator_id` longer than **100 characters** | `400` | `creator_id_too_long` |
  | `reasoning` missing or empty | `400` | `reasoning_missing` |
  | `reasoning` longer than **5,000 characters** | `400` | `reasoning_too_long` |
  | `attestation` missing or not exactly `true` (the string `"true"` doesn't count) | `400` | `attestation_required` |
  | `content_id` has no `decided` entry in the log | `404` | `content_not_found` |
  | `creator_id` doesn't match the original submission | `403` | `not_your_content` |
