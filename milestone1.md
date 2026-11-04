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

- **Who they are / what they wrote:**
- **What score they got:**
- **What the label said to them:**
- **What they can do about it:**

## 4. Endpoint contracts

### POST /submit

- **Request fields:**
- **Response fields (success):**
- **Response when input is bad:**

### POST /appeal

- **Request fields:**
- **Response fields (success):**
- **Response when content_id doesn't exist:**
