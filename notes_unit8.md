# Unit 8 working notes

Open threads to pick up later, in M4 (diagnosis), M5 (the one improvement) and
M6 (what's still broken). The finished write-up goes in README. This file is
for things not yet settled.

---

## MF07 / non-English text: my diagnosis so far

Chain of stages, as I worked it out after M2:

1. **Route.** `app.py:269` counts words with `text.split()`. The Arabic
   sentence has 17 space-separated words, so it passes `MIN_TEXT_WORDS = 5`.
   Nothing in the route checks whether the text is in a language the signals
   can read.
2. **Signal one.** GPT-2 is trained on English. On Arabic or Russian it
   produces a number (0.9064, 0.9531) that looks like a reading but probably
   isn't one.
3. **Signal two.** `stylometry.py:144` returns 0.5 when there are fewer than 3
   sentences. MF07 has 1 sentence, so this 0.5 comes from length, not
   language. The comment on that line says the fallback is handled in
   `scoring.combine_signals`, but `scoring.py` never handles it.
4. **Combining rule.** The disagreement cap (`scoring.py:57`) needs
   `|model - style| >= 0.5`. With style at 0.5, model would have to be exactly
   0.0 or 1.0, so the cap never fires. Once style abstains, the label depends
   on model alone: `0.7 × model + 0.3 × 0.5 >= 0.65` means `model >= 0.714`
   gives "ai". The 0.5 looks neutral, but in this rule it hands the whole
   decision to model. **I think this is the step that makes the mistake
   high-confidence.**

**Still to decide:**

- Which stage is *the* cause? "Why did it get in?" (route) and "why so
  confident?" (combining rule) are two different questions. The route fix
  only fixes non-English text. The combining-rule gap affects **every** text
  under 3 sentences, English included.
- The other style = 0.5 cases in the attack run, to check the pattern: EV07
  (unsure), EV08 (human), PI05 (unsure), FL01 (human). None was labelled ai
  only because model happened to stay under 0.714.

## Crash: MF04 and probe_ru3 (same bug)

- Both crash at `stylometry.py:72` with `ZeroDivisionError`, reached from
  `app.py:278`.
- Clues to work through:
  - `words()` uses `[a-z0-9']+`. How many words does it find in a Russian
    sentence? In `!!! ??? ...`?
  - `sentence_length_spread` divides by `statistics.mean(lengths)`. When is
    that 0?
  - The `len(lengths) < 2` guard only protects against fewer than 2
    sentences.
- **A crash writes no audit entry.** 56 attacks gave 55 log lines, and
  probe_ru3 is missing too. Unit 8's own warning applies here: "an attack that
  shows up only as an absence".
- The caller gets back Werkzeug's debugger HTML page, because debug mode is
  on.

## Chinese is rejected for the wrong reason

- `text.split()` gives 1 word for a whole paragraph, so the route answers 400
  `text_too_short`.
- Japanese and Thai, which also don't put spaces between words, would
  presumably do the same. Not tested yet.

## Not tested: RQ10 and RQ11

- Both counted against 127.0.0.1, because neither has a usable `creator_id`,
  and that address had already used up its 5 per minute. So both got 429
  before the route saw them.
- To test them properly: run them on their own, after a restart or more than
  a minute after any other request without a `creator_id`.

## Small things noticed

- 429 rejections don't record `endpoint`, but `reject()`'s 400s do.
- The `flood_same_creator` family's `targets` column says 20, but the file has
  12 rows.
