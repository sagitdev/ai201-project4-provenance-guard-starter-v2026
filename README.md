# Provenance Guard

> ### 👋 Start here
>
> **New to this repo? Read [RUNNING.md](RUNNING.md) first.**
>
> Once `python test.py` passes, in one terminal:
>
> ```bash
> python app.py
> ```
>
> and in another:
>
> ```bash
> curl -X POST http://127.0.0.1:5000/ping \
>   -H "Content-Type: application/json" \
>   -d '{"message": "hello"}'
> ```
>
> That's a web service. Something sent it text and it sent something back.
> Everything this unit is filling in the middle.
>
> **The rest of this file is your submission.** Fill it in as you go.

---

<!-- ─────────────────────────────────────────────────────────────────────────
     Unit 7 asks for the first five sections. Unit 8 adds the five below.

     Everything is pasted as TEXT. A pasted curl response gets full credit;
     a picture of your terminal gets none.
     ───────────────────────────────────────────────────────────────────────── -->

<!-- ═══════════════════════ UNIT 7 — THE BUILD ═══════════════════════ -->

## What This Does

<!-- The path a submission takes, from arriving to the label a reader sees.
     Six or seven steps — this is the trace you wrote in Milestone 1. -->

Provenance Guard is a small backend a writing site could plug into. Text comes
in; a guess, a score, a plain-English label and a way to appeal go out. The
path one submission takes through `POST /submit`:

1. **The request arrives.** `app.py::submit` parses the JSON body with
   `request.get_json(silent=True)`. Invalid JSON becomes `None`, not a crash.
2. **Validate, before anything expensive.** The request is rejected with a
   `400` (an `error` code plus a `message`) if the body isn't a JSON object,
   `creator_id` is missing or over 100 characters, or `text` is missing,
   empty, under 5 words or over 50,000 characters. Every check runs before the
   model is touched, and every rejection is written to the log with
   `audit.log_rejection`. Accepted text gets a `content_id` from
   `uuid.uuid4()`.
3. **Signal one — how predictable the text is.** `detector.py::model_signal`
   runs GPT-2 over the first 400 tokens, measures perplexity, and squashes it
   onto 0–1: low perplexity → high AI score.
4. **Signal two — the shape of the text.** `stylometry.py::style_signal`
   measures how much sentence lengths vary and maps that onto 0–1: even
   sentences → high AI score. With fewer than 3 sentences it returns a neutral
   0.5.
5. **Combine them.** `scoring.py::combine_signals` takes 0.7 × signal one +
   0.3 × signal two. If the two signals disagree by 0.5 or more, the score is
   capped just below the AI line, so the text can't be labeled AI.
6. **Turn the score into words.** `scoring.py::score_to_label`: up to 0.50 →
   human, 0.50–0.65 → unsure, 0.65 and above → AI, each with a full sentence a
   writer can read (see *Label Variants*).
7. **Record it, then answer.** `audit.py::log_decision` appends one line to
   `logs/audit.jsonl` with all three scores, the guess and the label; the
   response returns `content_id`, `guess`, `confidence`, `label`,
   `model_score` and `style_score`.

**The way back: `POST /appeal`.** A writer sends the `content_id`, their
`creator_id`, a reason and `attestation: true` ("this is my own writing").
After the format checks, the service confirms the `content_id` exists (`404`
if not) and belongs to them (`403` if not), then appends an `under_review`
entry beside the original decision — which is never edited — and confirms
that a person will review it.



---

## Signals and Scoring

<!-- For each signal: what property it measures, why that might differ between
     human and AI writing, and WHAT IT CAN'T SEE.

     The blind spot is not optional. If you can't name it you don't understand
     the signal yet — and unit 8's attack set is built out of blind spots. -->

### Signal one — the model signal

**What it measures:** How *predictable* the text is to a language model.
`detector.py` runs GPT-2 over the first 400 tokens and measures perplexity —
how surprised the model is by each next word — then squashes it onto 0–1 with
a logistic curve (perplexity 45 → 0.5). Low perplexity means a high AI score.

**Why that might differ between human and AI writing:** A language model
writes by repeatedly picking a likely next word, so text a model produced
tends to be text a model finds easy to predict. Human writing wanders more:
odd word choices, abrupt turns, mistakes. My own hand-written English scored
perplexity 62 (0.37); the AI-translated version of the same content scored 22
(0.76).

**What it can't see:** Predictability is not authorship.

- **Plain writers get accused.** Short sentences and common words are easy to
  predict whoever wrote them: second-language writers, children, step-by-step
  instructions, formulaic genres. My own cats text scored 0.79 on this signal
  — almost the AI texts' 0.82. These are the writers with the least room to
  argue back, and the problem is built into the method, not a fixable bug.
- **Quoted famous text** is something GPT-2 has seen countless times, so it
  reads as AI.
- **AI slips through when it's made less predictable.** Rare words, ornate
  prose, or a few added typos raise perplexity: my mistakes (*beacause*,
  *dosen't*) were a big part of why my text read as human, and the same
  trick works on AI text.
- It reads only the first 400 tokens, is unstable on short text, is a 2019
  English model, and says nothing meaningful about other languages.

### Signal two — the style signal

**What it measures:** The *shape* of the text, without reading a word: how
much sentence lengths vary — standard deviation ÷ mean of the words per
sentence (`stylometry.py::sentence_length_spread`). `style_signal` maps it
onto 0–1 with two anchors: spread ≤ 0.1 → 1.0 (AI-like), ≥ 0.6 → 0.0
(human-like), a straight line between, and a neutral 0.5 under 3 sentences.
Type-token ratio and punctuation density are also computed and printed, but
weighted 0: across ten samples, AI and my writing overlapped completely on
both (see *Calibration Log*, round 3).

**Why that might differ between human and AI writing:** "Most likely next
word" tends to produce even, mid-length sentences. Human writing is lumpier —
a four-word sentence next to a sixteen-word one. The most even AI text had a
spread of 0.11 (sentences of 11, 10, 13, 12 words); my cats text had 0.48.

**What it can't see:** It doesn't understand the content, so anything that
changes the shape without changing the substance moves it.

- **One keystroke moves it.** A missing space after a full stop (`them.I`)
  merges two sentences; one of my texts jumped to a spread of 0.98 that way.
  Splitting or merging a few sentences on purpose is a cheap way to make AI
  text look human.
- **Even writers get accused.** Academic or official prose, essays trained to
  keep "every sentence a moderate length", and instructions all have even
  sentence lengths. My music text (0.23) tied an AI text exactly.
- **Few sentences, fragile reading.** With three sentences, changing one
  moves it a lot: adding one opening sentence to my packages text dropped its
  spread from 0.47 to 0.21. Under 3 sentences it gives up and returns 0.5.
- It rests on a single measure, so there is no second style feature to catch
  what this one misses.

### The combining rule

<!-- Write the rule in words, then give the numbers. What happens when the two
     signals disagree? -->

**The rule:**

1. **Weighted average, leaning on signal one.** The combined score is mostly
   the model signal, with the style signal as a smaller second opinion.
2. **When the two signals strongly disagree, the text can't be labeled AI.**
   If the gap between them is at or above a set size, the score is capped
   just below the AI line, so the worst it can get is unsure. The rule only
   ever pushes *down*: a score already below the AI line is left alone, so it
   can never move someone from human to unsure.

In code terms:

```
score = 0.7 × model_score + 0.3 × style_score
if |model_score − style_score| ≥ 0.5:
    score = min(score, AI_THRESHOLD − 0.01)
```

**The numbers:**

| Setting | Value | Lives in |
|---|---|---|
| Model signal weight | 0.7 | `config.WEIGHT_MODEL_SIGNAL` |
| Style signal weight | 0.3 | `config.WEIGHT_STYLE_SIGNAL` |
| Disagreement gap | 0.5 | `config.py` |
| Cap when they disagree | just below `AI_THRESHOLD` (0.65 − 0.01) | `config.AI_THRESHOLD` |

**Why 0.7 / 0.3.** Round 3 showed signal one is the steadier of the two: AI
texts scored 0.82–0.89 on it, while the style signal's AI and human ranges
overlapped. So signal one gets more weight — but not too much, because the
heavier it is, the harder a signal-one false positive is to rescue. I tried
three weightings on the ten round 3 texts (AI line at 0.65):

| Weighting | H1 cats (mine) | A2 weekend (AI) | Result |
|---|---|---|---|
| 0.6 / 0.4 | 0.57 unsure ✅ | 0.64 unsure ❌ missed | safe, but lets AI through |
| **0.7 / 0.3** | **0.62 unsure ✅** | **0.68 AI ✅** | **the only one right on both** |
| 0.8 / 0.2 | 0.68 AI ❌ false positive | 0.73 AI ✅ | accuses a real writer |

At 0.7 / 0.3 none of my six pieces is labeled AI and all four AI texts are.
But the margin is thin: the cats text sits only 0.03 below the AI line. That
is what rule 2 is for.

**Why a disagreement rule at all.** In milestone 1 I decided that when the two
signals disagree, the answer should be unsure: two methods disagreeing *is*
uncertainty. A weighted average alone doesn't guarantee that — with signal
one weighted at 0.7, a text it strongly misreads can still go over the line.
The rule is one-sided because, as criterion 1 says, wrongly accusing a writer
costs far more than missing some AI text. The rule should only ever protect
people, never make anyone more suspect.

**Why the gap is 0.5.** I sorted the round 3 texts by the gap between their
two signals and looked for a line that rescues the text that needs it without
letting AI through:

| Text | model | style | gap | Truth | Should the rule fire? |
|---|---|---|---|---|---|
| H1 cats | 0.79 | 0.23 | **0.56** | mine | yes — signal one misreads it |
| A2 weekend | 0.82 | 0.36 | 0.46 | AI | no — must still be caught |
| A3 mom | 0.89 | 0.48 | 0.41 | AI | no |
| H3 music | 0.40 | 0.74 | 0.34 | mine | doesn't matter — already unsure |
| H5 weakness | 0.34 | 0.00 | 0.34 | mine | no — both signals say human |
| H4 packages | 0.49 | 0.78 | 0.29 | mine | doesn't matter |
| the other four | | | ≤ 0.19 | | no |

- Any line between 0.46 and 0.56 separates the cats text from the two AI
  texts. Below 0.46, the weekend text would escape the AI label too; above
  0.56, the cats text wouldn't be rescued.
- **0.5 sits in the middle**, leaving a similar margin on each side (0.06 for
  the cats text, 0.04 for the weekend text).
- It is also high enough not to fire on H5, whose signals differ by 0.34 but
  both point to human — a difference in degree, not a disagreement.
- **The honest limit:** this line rests on one text that needs rescuing and
  two that mustn't be. The cats text and the weekend text disagree in exactly
  the same direction (signal one says AI, style says human), and my signals
  can't truly tell them apart. 0.5 is a starting point that unit 8 will test,
  not a proven boundary.

**Not settled yet:** the label thresholds (0.35 / 0.65) are still the
placeholders. At 0.7 / 0.3 only one of my six pieces scores below 0.35; the
others land in unsure (0.43–0.62). Criterion 1 needs at least 7 of 10 labeled
human, so the human line has to be revisited in milestone 5.

**Where it lives:** `scoring.py::combine_signals`

<!-- ⚠️ The grader checks your code against that line. If your rule lives
     somewhere else, say where. -->

**A case where my two signals split, and what my rule does with it:**

**H1, my cats text** — written by hand, in short sentences with everyday
words: *"I have two cats. … They are street cats. Bingbing is almost 6 years
old."*

- Signal one: **0.79** (perplexity 19.7). GPT-2 finds plain writing easy to
  predict, so it reads this as AI — the milestone 1 false positive, on my own
  writing.
- Style signal: **0.23**. Sentence lengths run from 4 to 16 words (spread
  0.48), so it reads this as human.
- Weighted: 0.7 × 0.79 + 0.3 × 0.23 = **0.62** → unsure.
- Gap: 0.56 ≥ 0.5, so rule 2 fires. The score is already under the AI line,
  so nothing changes here. But the cats text is now protected even if the
  weights move: at 0.8 / 0.2 it would score 0.68, and the cap would hold it
  at 0.64, unsure.

A second split: the round 2 **mixed** text (my first three sentences, AI's
rewrite of the rest). Signal one 0.70, style 0.16 (spread 0.52), gap 0.54.
Weighted 0.54 → unsure, which is what criterion 3 asks of mixed writing.



---

## Calibration Log

<!-- My own record of testing both signals before deciding the style signal's
     weights. Not one of the five required sections. -->

Signal one is `detector.model_signal` (0–1, higher = more AI-like). Signal two
is reported here as its three raw measures from `stylometry.py`, before any
weighting:

- **spread** — sentence length standard deviation ÷ mean. Lower = more even
  sentences = expected to be more AI-like.
- **TTR** — unique words ÷ total words. Lower = more repetition = expected to
  be more AI-like.
- **punct** — commas, semicolons, colons, brackets, `!`, `?` and dashes per
  word. Direction not yet decided.

### Round 1

**The three texts**

1. **AI** — a chatbot-style paragraph:

   > Friendship is one of the most valuable aspects of human life. It provides
   > emotional support, companionship, and a sense of belonging. True friends
   > are there for us during difficult times and celebrate our successes. In
   > conclusion, nurturing friendships is essential for a happy and fulfilling
   > life.

2. **"Human"** — I treated this as my own writing at the time:

   > My hometown is Changzhi, a city in Shanxi Province, which has been named
   > the most charming city in Shanxi. Because it sits in a basin, it has four
   > distinct seasons: summers are never too hot, winters are never too cold,
   > and the city has a lot of green space. Many cities in Shanxi suffer from
   > serious air pollution because of the coal industry. Their winters are
   > often gray and hazy, and many people there develop rhinitis. Changzhi,
   > however, doesn’t have this problem.

3. **"Mixed"** — the first two sentences of text 2 kept, the rest rewritten by
   AI:

   > My hometown is Changzhi, a city in Shanxi Province, which has been named
   > the most charming city in Shanxi. Because it sits in a basin, it has four
   > distinct seasons: summers are never too hot, winters are never too cold,
   > and the city has a lot of green space. Because of the coal industry, many
   > cities in Shanxi struggle with heavy air pollution. Their winters are
   > often gray and smoggy, and rhinitis is common among residents. Changzhi is
   > an exception: its air stays relatively clean.

**Results**

| Text | perplexity | model_signal | spread | TTR | punct | sentence lengths (words) |
|---|---|---|---|---|---|---|
| 1. AI | 17.0 | **0.83** | **0.11** | 0.83 | 0.065 | 11, 10, 13, 12 |
| 2. "Human" | 21.7 | **0.76** | **0.52** | 0.70 | 0.108 | 19, 30, 14, 13, 7 |
| 3. "Mixed" | 21.0 | **0.77** | **0.48** | 0.68 | 0.106 | 19, 30, 14, 13, 9 |

**What I concluded at the time**

- **Signal one barely separated "my" writing from AI** (0.76 vs 0.83). I read
  this as proof of the second-language blind spot from milestone 1.
- **The "mixed" text scored almost the same as the "human" one** (0.77 vs
  0.76) on both signals. Its sentence lengths are nearly identical too.
- **Spread separated AI from human clearly** (0.11 vs 0.52).
- **TTR pointed the wrong way:** AI 0.83, higher than "mine" at 0.70. Since
  TTR falls with length (46 vs 83 words), I re-measured on equal lengths. It
  still pointed the wrong way:

  | | full TTR | first 40 words | moving 40-word average |
  |---|---|---|---|
  | AI | 0.83 | 0.90 | 0.88 |
  | "Human" | 0.70 | 0.75 | 0.79 |

  The "human" text reuses its key words (*Shanxi* ×3, *city/cities* ×3); the
  AI deliberately varies them (*companionship*, *belonging*, *nurturing*).
- **Punct looked like "more punctuation = more human"** (0.108 vs 0.065).

### What I clarified, and why I rewrote the texts

Text 2 was **not written by me in English**. I wrote it in Chinese and had
AI translate it into English. The ideas were mine; every English word was
chosen by an AI.

That invalidated round 1's "human" sample:

- Signal one's 0.76 on it was not a false positive — it was largely *right*.
  The words really were AI-generated.
- Every conclusion drawn by comparing "human" against AI was comparing AI
  against AI. It also explains why the "mixed" text barely differed from the
  "human" one: both halves of it were AI-written words.

So I wrote text 2 again, entirely by hand in English, with no tools, and
rebuilt text 3 from it. Text 1 stayed the same.

### Round 2

**The three texts**

1. **AI** — unchanged from round 1.

2. **Human** — written entirely by me, in English. The spelling and grammar
   mistakes are mine and were left in:

   > My hometown is Changzhi which belongs to Shanxi province. Changzhi is
   > prized as the most charming city in Shanxi. It has four seasons clearly,
   > and it is not very hot in summer or very cold in winter. Mostly probably
   > beacause it located in a basin. The city has a lot of green plants,and it
   > dosen't has seriouse air pollution. But many other cities has very gray
   > and smoggy winter beacuse of thr coal industry.

3. **Mixed** — the first three sentences of text 2 kept, the rest rewritten
   by AI:

   > My hometown is Changzhi which belongs to Shanxi province. Changzhi is
   > prized as the most charming city in Shanxi. It has four seasons clearly,
   > and it is not very hot in summer or very cold in winter. This is
   > probably because the city sits in a basin. Changzhi has plenty of
   > greenery and doesn’t suffer from serious air pollution, unlike many other
   > cities in Shanxi, where the coal industry brings gray, smoggy winters.

**Results**

| Text | perplexity | model_signal | spread | TTR | punct | sentence lengths (words) |
|---|---|---|---|---|---|---|
| 1. AI | 17.0 | **0.83** | **0.11** | 0.83 | 0.065 | 11, 10, 13, 12 |
| 2. Human (my own English) | 62.1 | **0.37** | **0.32** | 0.71 | **0.027** | 9, 10, 18, 8, 15, 15 |
| 3. Mixed | 26.2 | **0.70** | **0.52** | 0.76 | 0.054 | 9, 10, 18, 10, 27 |

**What I found**

- **Signal one now reads my writing as human-leaning (0.37)**, against 0.76
  for the AI-translated version of the same content. Perplexity rose from 22
  to 62 because of my mistakes — *beacause*, *dosen't*, *seriouse*, *thr*,
  *it dosen't has*. GPT-2 has never seen these, so it can't predict them.
  This cuts both ways:
  - a real second-language writer's natural mistakes protect them;
  - adding a few typos to AI text would fool signal one the same way — the
    milestone 1 blind spot;
  - a second-language writer who writes carefully *without* mistakes is
    still at risk: "I go to school every day…" from milestone 1 scored 0.89.
- **Replacing half my writing with AI's pushed signal one from 0.37 to
  0.70.** The AI's rewrite fixed the mistakes and used tidy, predictable
  wording.
- **Text 3 is a case where the two signals split.** Signal one says AI
  (0.70). Signal two's spread says human (0.52) — *more* human than my own
  writing (0.32), because the AI merged my last two sentences into one
  27-word sentence, so sentence lengths vary more. Under my rule — when the
  signals disagree, the answer is unsure — this lands in unsure, which is
  what criterion 3 asks of mixed writing.
- **Punct reversed direction.** My real writing has the *least* punctuation
  of the three (0.027, under half the AI's 0.065). Round 1's "more
  punctuation = more human" came entirely from AI-translated text. Had I
  coded that direction, my own writing would have scored as fully AI-like on
  this measure.
- **TTR still points the wrong way** (AI 0.83 > mixed 0.76 > mine 0.71;
  moving 40-word average 0.88 > 0.82 > 0.77) — now with genuinely human
  text. I repeat *Changzhi*, *Shanxi*, *very*, *cities*; the AI varies its
  words. The finding holds: TTR would accuse second-language writers.
- **Spread is still the most reliable measure** — AI 0.11 against 0.32 and
  0.52.

### A side observation: one missing space

In an earlier run, text 3 of round 1 was typed as `green space.Because` — no
space after the full stop. `sentences()` splits on a full stop *followed by
a space*, so it merged two sentences into one, and spread jumped from 0.48 to
0.74. One deleted space moves the style signal: exactly the "changes the
shape, not the substance" blind spot, and a very cheap attack for unit 8.

### Lessons

- **The provenance of test data decides everything.** One mislabeled sample
  produced a conclusion that turned out to be backwards. Test writing has to
  be genuinely mine — which is what `scenarios.py` warns about.
- **One sample per category can't set a direction.** A rule fitted to one
  example only memorises that example (overfitting). Punct showed this:
  swap one sample and its direction flipped.
- **AI translation is a grey area this system can't resolve.** Writing in
  Chinese and having AI translate it means the ideas are human and the words
  are AI. Signal one can only see the words, so it will lean AI — which is
  "correct" from the system's view and unfair from the writer's. Many
  non-native writers work exactly this way. The system can't know a Chinese
  draft exists; what it can do is avoid accusing (the unsure label) and let
  the writer explain in an appeal, for a human reviewer to judge against the
  site's own rules.

### Deciding the style signal's weights

The style signal has to output one 0–1 score, so I need a direction and a
weight for each measure. Where round 2 leaves each one:

| Measure | Status | Why |
|---|---|---|
| spread | **use it** | Direction is clear and held in both rounds (AI 0.11 against 0.32 and 0.52). |
| TTR | **weight 0** | Points the wrong way in both rounds, even at equal lengths. Using it would push second-language writers toward AI. |
| punct | **undecided** | Flipped direction when one sample changed (0.108 → 0.027). One sample per category can't settle it. |

So the open question is punct: gather more data to set its direction, or
leave it out for now.

**Option A — gather more texts first.** Write 2–3 more AI texts (different
chatbots or prompts) and 2–3 more of my own, by hand in English, at least
3 sentences and 50 words each. Run them all through `stylometry.py` and set
punct's direction from what most samples show.

- *For:* the direction rests on evidence, not one sample. My own pieces are
  needed for criterion 1 anyway (10 hand-written pieces), so none of the
  writing is wasted.
- *Against:* 20–30 more minutes of writing before coding.

**Option B — spread only, for now.** Keep computing and printing all three
measures, but weight spread 1.0, TTR 0 and punct 0. Revisit after the four
calibration inputs in milestone 4.

- *For:* coding continues straight away.
- *Against:* the style signal rests on one measure, which is fragile — one
  missing space moved spread from 0.48 to 0.74. The brief also asks the style
  signal to "compute two or three things … and combine them".

**Decision: option A.** I've already seen what one sample does to a
direction: had I coded round 1's "more punctuation = more human", my own
writing would have scored fully AI-like on punct. A style signal resting on a
single measure is also too easy to fool. And the hand-written pieces feed
straight into criterion 1.

### Round 3

**The new texts.** Three AI texts and five of my own, plus the two from
round 2. The AI texts were written by a chatbot from ordinary prompts (*why
reading is important*, *a typical weekend*, *my mom*). I removed their title
lines before scoring: a title has no full stop, so `sentences()` would glue it
onto the first sentence. My five were written by hand in English; mistakes
are mine and were left in.

- **H1 cats** — *"I have two cats. One is a white cat called Bingbing,
  another is an orange cat called Lucky. … They are street cats. …"*
- **H2 retail** — *"I worked for six years in the luxury retail industry, so I
  know the retail field very well …"*
- **H3 music** — *"I love pop music, new Jazz and some classic American
  country music. For artists, I like Westlife, Backstreet Boy, Avril, Tyler
  Swift, and Black Pink. …"*
- **H4 packages** — *"During my first course in the master program, I really
  hope to create something that solves a real problem. …"*
- **H5 weakness** — *"Sometimes I focus too much on supporting others. …
  sometimes I put my own tasks aside to help them.I realized this affect my
  efficiency …"*

**Results**

| Text | words | perplexity | model_signal | spread | TTR | punct | sentence lengths |
|---|---|---|---|---|---|---|---|
| H0 Changzhi (round 2) | 75 | 62.1 | 0.37 | 0.32 | 0.71 | 0.027 | 9, 10, 18, 8, 15, 15 |
| H1 cats | 76 | 19.7 | **0.79** | 0.48 | 0.67 | 0.039 | 4, 14, 9, 6, 4, 10, 13, 16 |
| H2 retail | 62 | 36.5 | 0.58 | 0.32 | 0.76 | 0.048 | 28, 19, 15 |
| H3 music | 77 | 58.3 | 0.40 | 0.23 | 0.78 | **0.130** | 12, 13, 13, 8, 14, 17 |
| H4 packages | 71 | 46.4 | 0.49 | 0.21 | 0.75 | 0.070 | 19, 23, 29 |
| H5 weakness | 82 | 69.1 | 0.34 | **0.98** | 0.74 | 0.085 | 8, **58**, 16 |
| A0 friendship (round 1) | 46 | 17.0 | 0.83 | 0.11 | 0.83 | 0.065 | 11, 10, 13, 12 |
| A1 reading | 98 | 17.3 | 0.82 | 0.23 | 0.73 | 0.102 | 12, 16, 19, 21, 12, 18 |
| A2 weekend | 101 | 17.1 | 0.82 | 0.42 | 0.75 | 0.079 | 11, 18, 23, 18, 4, 13, 14 |
| A3 mom | 101 | 12.1 | 0.89 | 0.36 | 0.75 | 0.079 | 12, 10, 25, 17, 23, 14 |

**What I found**

- **Punct can't separate the groups, in either direction.** Mine range
  0.027–0.130; the AI's 0.065–0.102 sit entirely inside that. My music text
  has the most punctuation of all ten, because it lists five artists with a
  comma after each. How much punctuation a text has depends on *what* it says
  (a list, a run of experiences), not on who wrote it.
- **TTR overlaps too** — AI 0.73–0.83, mine 0.67–0.78. Weight 0 confirmed.
- **Spread is the best of the three, but weaker than rounds 1–2 suggested.**
  AI 0.11–0.42, mine 0.21–0.48 (leaving out H5). My music text (0.23) ties
  the reading text exactly. One short AI sentence — *"Sunday is more
  relaxed."* — lifted the weekend text to 0.42.
- **With few sentences, spread is fragile.** An earlier draft of H4 scored
  0.47; adding one 19-word opening sentence dropped it to 0.21. An earlier
  two-sentence piece scored 0.16, more "even" than any AI text — two numbers
  give no meaningful spread.
- **The missing-space problem happened in real writing.** H5's `help
  them.I realized` merged two sentences into a 58-word one, so spread jumped
  to 0.98. Here it happened to help me; it is still a one-keystroke way to
  move the score.
- **H1 is the milestone 1 false positive, on my own writing.** Short
  sentences and everyday words: signal one gives it 0.79, almost the AI
  texts' 0.82. Only spread (0.48, human-leaning) disagrees. Under my rule —
  signals disagree → unsure — that disagreement is what keeps it out of the
  AI label. It is the clearest reason the system needs a second signal.
- **Signal one carries most of the separation.** AI 0.82–0.89, very steady;
  mine 0.34–0.58 apart from H1. So when I combine the signals, signal one
  probably needs more than half the weight.

### Final decision for the style signal

**Spread only: weight 1.0, TTR 0, punct 0.** All three measures are still
computed and printed by `python stylometry.py`, so I can keep watching them.
This is now a conclusion from ten samples, not an assumption: the measures I
dropped overlapped completely, and keeping them would only add noise. It does
leave the style signal resting on one fragile measure — the missing-space
attack above — which I expect unit 8 to exploit.

`stylometry.py::style_signal` maps spread onto 0–1 with two anchors and a
straight line between them:

| spread | style_signal | meaning |
|---|---|---|
| ≤ 0.1 | 1.0 | very even sentences — AI-like |
| 0.1 – 0.6 | `(0.6 − spread) / 0.5` | in between, proportionally |
| ≥ 0.6 | 0.0 | very uneven sentences — human-like |
| fewer than 3 sentences | 0.5 | neutral: too few sentences for spread to mean anything |

The anchors come from the data: the most even AI text is 0.11, and only my
writing went above 0.6. Checks: the cats text gives 0.232; a two-sentence
text gives 0.5.

### The four calibration inputs

With both signals and the combining rule wired into `/submit` (weights
0.7 / 0.3, disagreement gap 0.5), I sent the four calibration inputs through
the running service. The label thresholds are still the placeholders
(below 0.35 human, above 0.65 AI).

The lightly edited AI text is the round 3 *mom* text with my own edits
(roughly 10–20%): I split one sentence in two (*"I never heard her complain
about this."*), and changed a few words and phrases (*strength → power*,
*often → every day*, *when things get difficult → when I meet
difficulties*).

| Input | Text | model | style | gap | confidence | Lands in | As intended? |
|---|---|---|---|---|---|---|---|
| Clearly AI | A1 reading | 0.82 | 0.74 | 0.08 | **0.80** | AI | ✅ |
| Clearly human | H0 Changzhi | 0.37 | 0.55 | 0.18 | **0.43** | unsure | ⚠️ should be human |
| Plain human | H1 cats | 0.79 | 0.23 | 0.56 | **0.62** | unsure | ✅ not accused |
| Lightly edited AI | A3 mom, edited | 0.86 | 0.45 | 0.41 | **0.74** | AI | ✅ (see below) |

**What each one shows**

- **Clearly AI (0.80):** both signals agree (gap 0.08), so the system is
  confident, and right.
- **Clearly human (0.43):** the biggest problem left. This text is full of my
  spelling mistakes and is obviously human, yet it doesn't reach the human
  label. The signals are not the issue: the human line (0.35) is too low.
  That is the threshold question noted under *The combining rule*, for
  milestone 5.
- **Plain human (0.62):** signal one misreads it (0.79), the style signal
  disagrees (0.23), and the combination stops in unsure. The two signals
  checking each other works as designed — but only 0.03 below the AI line.
- **Lightly edited AI (0.74):** my edits barely moved it.

  | | original A3 | my edited version |
  |---|---|---|
  | model | 0.89 | 0.86 |
  | spread | 0.36 | 0.37 |
  | confidence | 0.77 | 0.74 |

  Light editing doesn't fool the system: most of the sentence structure and
  wording are still the AI's, and signal one still recognizes them. I think
  labeling it AI is acceptable, since over 80% of it is still AI-written. It
  does point at a grey area, though: a real user might let AI write a draft
  and then edit it, and the system treats that as AI. How much editing it
  takes to cross the line is something unit 8 is likely to probe.

---

## Label Variants

<!-- The exact text of all three labels, as a reader would see them, and the
     score range each covers.

     Write them for someone who has never heard the word "threshold". -->

| Label | Score range | The exact text a reader sees |
|---|---|---|
| high-confidence human | 0.00 – 0.50 | We think this was most likely written by a person. |
| unsure | 0.50 – 0.65 | We can't tell how this was written — our check has its limits. Nothing happens because of this result. If you'd like a person to take a look, you can request a review. A review can make the result more objective. |
| high-confidence AI | 0.65 – 1.00 | We think this was most likely written by AI. Nothing happens because of this result. If you think this result is wrong, you can request a review. A person can see things our check can't. |

The text lives in `scoring.py::score_to_label`; the ranges come from
`config.HUMAN_THRESHOLD` and `config.AI_THRESHOLD` (`scoring.label_ranges()`
prints them). A score exactly on a line goes to the outer label: 0.50 is
human, 0.65 is AI. The disagreement cap (0.64) always lands in unsure. All
three labels were reached through `/submit`: my Changzhi text → human (0.43),
my cats text → unsure (0.62), the AI reading text → AI (0.80).

### Where the lines are, and why

All final scores so far, at weights 0.7 / 0.3:

| Text | Score | Truth |
|---|---|---|
| H5 weakness | 0.24 | mine |
| H0 Changzhi | 0.43 | mine |
| H3 music | 0.50 | mine |
| mixed (round 2) | 0.54 | half mine, half AI |
| H2 retail | 0.57 | mine |
| H4 packages | 0.58 | mine |
| H1 cats | 0.62 | mine |
| A2 weekend | 0.68 | AI |
| A3 mom, lightly edited | 0.74 | AI |
| A3 mom | 0.77 | AI |
| A1 reading | 0.80 | AI |
| A0 friendship | 0.88 | AI |

- **AI line stays at 0.65.** My highest piece is 0.62, the lowest AI text
  0.68, and 0.65 sits in the middle of that gap (0.03 margin each side).
- **Human line moves from 0.35 to 0.50.** At 0.35 only one of my six pieces
  was labeled human. But the line can't go high enough to cover them all:
  my pieces at 0.57 and 0.58 sit right next to the mixed text at 0.54.
  Criterion 1 wants most of my writing labeled human; criterion 3 wants mixed
  writing labeled unsure. No single line satisfies both.
- **I chose to keep mixed writing in unsure.** My own writing landing in
  unsure is not an accusation — the label says nothing happens because of
  it. Mixed writing labeled human would mean "let AI write half, then edit"
  passes as human, and the tool stops catching what it exists to catch.
  Between 0.45 and 0.50 I took 0.50: one more of my pieces gets recognized as
  human, and the mixed text is still in unsure.
- **What it costs:** criterion 1 needs at least 7 of 10 of my pieces labeled
  human; with this line only 3 of 6 are (H3 sits exactly on 0.50). I expect
  to miss criterion 1 in unit 8, and I'm not lowering it. The mixed text has
  only 0.04 of margin and it's a single sample — criterion 3's three mixed
  pieces may move this line. Most of my own writing will see the unsure
  label, so that label's wording matters most.

**Why I worded the "unsure" one this way:**
<!-- It's the hardest of the three. It has to admit uncertainty without
     sounding like an accusation, because the person reading it may well have
     written every word themselves. -->

Because of where I put the human line, unsure is the label my own writing
gets most often. So it had to put the doubt on the *tool*, not the writer,
and make clear nothing follows from it.

- *"Our check has its limits"* gives the reason for the uncertainty and
  places it on our side. It deliberately doesn't say which features caused
  it: a reader would wonder whether to change how they write, and anyone
  else would learn how to get around the check.
- *"Nothing happens because of this result"* — a fact, not a reassurance.
  Readers trusted it more than anything else in the label.
- *"Request a review"*, not "appeal": nothing was claimed against them, so
  there's nothing to appeal against. The AI label uses the same words, so a
  reader sees one action, not two.
- No percentage. A number like "62%" means nothing to a writer, and since
  scores mean "AI-likeness", a human label would show a low number that reads
  as "we're barely sure you wrote this".

### How the wording changed: three versions, two reader tests

I wrote a first draft (in Chinese) that said *"This is human-written / AI-
written, system confidence X%"* and promised a result within 24 hours. Four
problems: it showed a number; it claimed certainty no detector has; the
unsure label said "not sure whether you used AI tools", which points the
doubt at the writer; and "24 hours" promised something the system can't do
— `/appeal` only records the appeal. The review is a person, outside this
service.

I then tested the labels the way the brief suggests: pasting them into a
fresh AI chat and asking it to answer *as the writer*, "what is this saying
about me, and what would I do next?"

| Version | What the "writer" heard | What I changed |
|---|---|---|
| **v1** | Unsure read as *"you didn't quite pass"*. *"This isn't a judgement about you"* made it sound like one. *"Some of its features"* made them wonder if their writing was the problem. They wouldn't ask for a review, afraid it could end in the AI label. The AI label's *"especially for writing that is very simple or very regular"* felt like an insult to plain or second-language writers. | Dropped "not a judgement"; replaced the feature hint with "our check has its limits"; added "a review can't make the result worse"; changed the AI label's subject to *our check* ("Our check is sometimes wrong"); "if you wrote it yourself" → "if you think this result is wrong", so someone who used a grammar tool still feels entitled to ask; one term, "request a review". |
| **v2** | Unsure: *"the problem is their tool, not me"*, and they'd ask for a review without hesitating. But the AI label's *"No action is taken on this result unless a person has reviewed it"* read as *"a review is what triggers action"*, so a writer with any doubt would avoid asking. | Removed that sentence; the AI label now says the same as unsure: *"Nothing happens because of this result."* |
| **final** | — | My own last edits (below). |

**Choices I made against the test's advice, knowingly:**

- In unsure, I replaced *"A review can't make the result worse"* with *"A
  review can make the result more objective."* The v2 reader said the old
  line removed their biggest worry. I preferred to say what a review adds
  rather than what it can't do; the worry it answered may come back.
- In the AI label, I replaced the same line with *"A person can see things
  our check can't"*, and dropped *"Our check is sometimes wrong"* — "most
  likely" and "if you think this result is wrong" already carry that.
- I rejected *"a review will give you a satisfying result"*: if the text
  really is AI-written, the reviewer won't change it, so that's a promise the
  system can't keep.

**What the labels don't say, and why:**

- **Who can see the label.** Both reader tests named this as their biggest
  question. The service is only an API — it has no idea of who sees what —
  so any answer would be a promise the code doesn't keep. Left out on
  purpose; it belongs to whatever site uses this service.
- **"Nothing happens because of this result"** (unsure and AI) is a policy
  assumption, not something the code enforces. It's true of this service —
  it never hides or removes anything — but if a site ever acts on the
  labels, this sentence has to change.

---

## Sample Run

<!-- One submission and one appeal, pasted as text: the request, the response,
     and the log entries. -->

My cats text, written by hand: signal one misreads its plain sentences as
AI, the style signal disagrees, and it lands in unsure. Then I ask for a
review.

**A submission**

<!-- The response needs content_id, guess, confidence, label, AND both
     signal scores - model_score and style_score. Unit 8's tools read those
     two off the response, so leaving them out costs you next unit's
     diagnostics. -->

```bash
$ curl -X POST http://localhost:5000/submit \
  -H "Content-Type: application/json" \
  -d '{"text": "I have two cats. One is a white cat called Bingbing, another is an orange cat called Lucky. Lucky is older and 8 years old right now. Bingbing is almost 6 years old. They are street cats. When I met Lucky, he was only 2 months old. Bingbing was thrown in an elevator by someone and only 1 month old. I love and really miss them, because they are living with my parents in China now.", "creator_id": "tank"}'
```

```json
{
  "confidence": 0.622,
  "content_id": "981daedc-db90-425f-b1a8-e529d027f072",
  "guess": "unsure",
  "label": "We can't tell how this was written \u2014 our check has its limits. Nothing happens because of this result. If you'd like a person to take a look, you can request a review. A review can make the result more objective.",
  "model_score": 0.7891,
  "style_score": 0.232
}
```

(`\u2014` is how Flask's JSON writes the dash "—".)

**An appeal**

```bash
$ curl -i -X POST http://localhost:5000/appeal \
  -H "Content-Type: application/json" \
  -d '{"content_id": "981daedc-db90-425f-b1a8-e529d027f072", "creator_id": "tank", "reasoning": "I wrote this myself about my two cats. The sentences are short because I write simply in English.", "attestation": true}'
```

```
HTTP/1.1 200 OK
Content-Type: application/json
```

```json
{
  "content_id": "981daedc-db90-425f-b1a8-e529d027f072",
  "message": "We've received your appeal. A person will review it.",
  "status": "under_review"
}
```

**Invalid appeals**, all on the same `content_id`, sent right after:

| Request | Status | `error` |
|---|---|---|
| `creator_id: "someone_else"` | 403 | `not_your_content` |
| `attestation: false` | 400 | `attestation_required` |
| `content_id: "does-not-exist"` | 404 | `content_not_found` |
| `reasoning` of 5,001 characters | 400 | `reasoning_too_long` |
| no `creator_id` | 400 | `creator_id_missing` |

**What the log shows afterwards**

```bash
$ curl "http://localhost:5000/log?limit=8"
```

```json
{
  "count": 8,
  "entries": [
    {
      "combined_score": 0.622,
      "content_id": "981daedc-db90-425f-b1a8-e529d027f072",
      "creator_id": "tank",
      "guess": "unsure",
      "label": "We can't tell how this was written \u2014 our check has its limits. Nothing happens because of this result. If you'd like a person to take a look, you can request a review. A review can make the result more objective.",
      "model_score": 0.7891,
      "status": "decided",
      "style_score": 0.232,
      "timestamp": "2026-11-11T02:11:16+00:00"
    },
    {
      "combined_score": 0.7989,
      "content_id": "84881bb9-5539-4f8c-a589-6d7c108cb9f2",
      "creator_id": "tank",
      "guess": "ai",
      "label": "We think this was most likely written by AI. Nothing happens because of this result. If you think this result is wrong, you can request a review. A person can see things our check can't.",
      "model_score": 0.8224,
      "status": "decided",
      "style_score": 0.744,
      "timestamp": "2026-11-11T02:11:24+00:00"
    },
    {
      "content_id": "981daedc-db90-425f-b1a8-e529d027f072",
      "creator_id": "tank",
      "event": "appeal",
      "reasoning": "I wrote this myself about my two cats. The sentences are short because I write simply in English.",
      "status": "under_review",
      "timestamp": "2026-11-11T02:36:32+00:00"
    },
    {
      "creator_id": "someone_else",
      "endpoint": "/appeal",
      "event": "rejected",
      "reason": "not_your_content",
      "status": "rejected",
      "timestamp": "2026-11-11T02:36:46+00:00"
    },
    {
      "creator_id": "tank",
      "endpoint": "/appeal",
      "event": "rejected",
      "reason": "attestation_required",
      "status": "rejected",
      "timestamp": "2026-11-11T02:37:00+00:00"
    },
    {
      "creator_id": "tank",
      "endpoint": "/appeal",
      "event": "rejected",
      "reason": "content_not_found",
      "status": "rejected",
      "timestamp": "2026-11-11T02:37:09+00:00"
    },
    {
      "creator_id": "tank",
      "endpoint": "/appeal",
      "event": "rejected",
      "reason": "reasoning_too_long",
      "status": "rejected",
      "timestamp": "2026-11-11T02:37:42+00:00"
    },
    {
      "creator_id": null,
      "endpoint": "/appeal",
      "event": "rejected",
      "reason": "creator_id_missing",
      "status": "rejected",
      "timestamp": "2026-11-11T02:37:49+00:00"
    }
  ]
}
```

What to check in it:

- The original `decided` entry for `981daedc…` is unchanged — same score,
  same label, same timestamp. The appeal didn't overwrite it.
- Exactly **one** new entry for that `content_id`: `event: "appeal"`,
  `status: "under_review"`, carrying the reasoning. The item's current status
  is its latest entry, so it is now under review.
- The five invalid appeals left only `rejected` entries — none of them
  produced an `under_review` entry (criterion 4).

### Reading the log: entries written before and after a format change

The log is append-only, so entries written by older code keep their old
shape. One change matters when reading it:

- **`endpoint` on rejections.** From milestone 5, every `rejected` entry
  records which route refused it (`/submit` or `/appeal`), because both can
  return the same error codes (`invalid_json`, `creator_id_missing`). The one
  rejection written earlier (`text_missing`, 2026-11-10T04:55:24) has no
  `endpoint` field; it came from `/submit`, the only route that existed then.
- **`creator_id: null` on rejections.** From the same change, a rejection
  with no usable `creator_id` (missing, not a string, or over 100
  characters) records `null`, never a placeholder string. A placeholder like
  `"unknown"` could be a real writer's id; a real id is always a non-empty
  string, so `null` can't be mistaken for one. (No rejection in this log was
  written under the older placeholder rule.)
- Decisions from milestones 3–4 also show their stage: `style_score: null`
  (M3, signal one only) and `label: "PLACEHOLDER"` (M3–M4, before the labels
  existed).

---

## How I Used AI

**Moment 1 — the label wording (milestone 5)**

- *What I asked for:* I wrote the three labels myself, in Chinese, and asked
  Claude to check them. My draft said things like *"This text is AI-written,
  system confidence X%. You can appeal and we'll check it by hand within 24
  hours."*
- *What came back:* Four problems. The percentage would mislead: scores mean
  AI-likeness, so a human label would show a small number that reads as
  "we're barely sure you wrote this". "Is AI-written" claims a certainty no
  detector has. My unsure label ("not sure whether you used AI tools") pointed
  the doubt at the writer. And "24 hours" was a promise the service can't
  keep — `/appeal` only records the appeal. It drafted a revised version. I
  then ran the brief's reader test twice, each time in a fresh AI chat that
  knew nothing about my system, asking it to answer *as the writer*.
- *What I changed:* I took the fixes the tests justified: dropped "this isn't
  a judgement about you", which the first test said made it sound like one;
  put the cause on "our check" instead of the writer's features; removed "no
  action is taken unless a person has reviewed it", which the second test
  read as "asking for a review triggers action". But some decisions went
  against the advice. I replaced "a review can't make the result worse" with
  my own "a review can make the result more objective", even though the
  tester said the old line removed their biggest worry. I dropped "our check
  is sometimes wrong" from the AI label. I wanted to promise "a review will
  give you a satisfying result" and was talked out of it, because if the text
  really is AI-written that promise breaks. And I chose to say nothing about
  who can see the label, though both tests asked, because the service has no
  way to keep that promise. The full before-and-after is under *Label
  Variants*.

**Moment 2 — the "human" sample that wasn't (milestone 4)**

- *What I asked for:* I ran three texts — an AI paragraph, "my own"
  paragraph about my hometown, and a mixed one — through both signals and
  asked Claude to analyse the numbers so I could decide the style signal's
  weights.
- *What came back:* A confident analysis. Signal one barely separated my
  writing from the AI's (0.76 vs 0.83), which it read as proof of the
  second-language blind spot from milestone 1. Punctuation looked like "more
  punctuation = more human" (0.108 vs 0.065). Type-token ratio pointed the
  wrong way. All of it followed logically from the data.
- *What I changed:* The data was wrong, and only I knew it. My "own"
  paragraph wasn't written in English by me: I wrote it in Chinese and had AI
  translate it. Every English word was the AI's, so the analysis was comparing
  AI against AI. I told Claude, wrote the paragraph again entirely by hand in
  English — mistakes left in — and reran everything. Signal one dropped from
  0.76 to 0.37, and punctuation flipped direction: my real writing had the
  *least* punctuation of the three. Had I coded the first conclusion, my own
  writing would have scored as fully AI-like on that measure. After that I
  wrote more samples (round 3), and punctuation turned out not to separate
  the groups at all, so it got weight 0. The lesson I kept: an AI's analysis
  is only as good as the data it's given, and it can't know where my data
  came from. Both rounds are recorded in the *Calibration Log*.

<!-- ═══════════════════════ UNIT 8 — THE TEST ═══════════════════════ -->

---

## Rate Limiting

**My limits:** 5 per minute, 50 per day

**Why those numbers and not others:**

- **5 per minute** stops bursts. A writer who changes a word and resubmits to
  see the new score can do that 3 to 5 times in a minute at most. Anything
  faster isn't someone reading the results. It also has to sit between two
  hard limits: below 15, so `--flood 15` shows a 429, and at least 3, because
  `run_eval.py` sends the same creator_id three times in a row, once per trial.
- **50 per day** stops threshold mapping, which depends on the total number of
  tries, not their speed. A very busy writer submits about 3 pieces a day and
  revises each about 5 times, so around 15 submissions. 50 leaves 2 to 3 times
  headroom. A script that wants to try 1,000 variations needs 20 days at 50 a
  day. The starter's default of 200 a day would let it finish in 5.

**What a caller counts as:** per `creator_id`, falling back to the caller's
address when `creator_id` is missing, empty, not a string or over 100
characters (`rate_limit_key` in `app.py`). This only stops a script that keeps
one identity. `creator_id` is whatever the caller writes, so a script that
sends a new one with every request looks like a thousand different writers and
never hits the limit. Per-address limiting would catch that script, but it
would also put a whole household or classroom behind one shared address under
a single limit. Neither choice fixes the real problem, which is that the caller
picks their own identity. The limit counts are also kept in memory, so a
restart resets them.

**The run of status codes when I pushed past it:**

<!-- python run_attacks.py --flood 15 -->

```
200 200 200 200 200 429 429 429 429 429 429 429 429 429 429
```

The first 5 submissions within one minute were judged, and requests 6 to 15
were rejected. All 10 rejections are in `logs/audit.jsonl` as
`"reason": "rate_limited", "limit": "5 per 1 minute"`.

**What I considered and left out: a cooldown after a 429.** The limit resets
60 seconds after the first request in the window, so a caller who hits the
limit can carry on a minute later. I considered adding a penalty, where hitting
the limit blocks that caller for 10 minutes. Flask-Limiter doesn't do this, so
it would need my own code: record an "unblocked at" time on every 429, check it
at the top of `/submit`, and send a `Retry-After` header so the caller knows how
long to wait. I didn't add it, for three reasons:

- **Most of the cost lands on real writers.** A writer who clicks submit one
  time too many would be locked out for 10 minutes, for a single slip.
- **It doesn't stop the attack it's aimed at.** A script that sends a new
  `creator_id` with every request never hits the limit, so it never gets the
  cooldown either.
- **The daily cap already does that job.** Threshold mapping depends on the
  total number of tries. 50 a day makes 1,000 tries take 20 days, whatever the
  pace within a day.

**Future work:** add the cooldown once callers have identities they can't make
up themselves, such as logged-in accounts. Then a lockout would actually land
on the person who caused it. The length should grow with each repeat (1 minute,
then 10, then an hour), so one slip costs little and repeated flooding costs a
lot. That needs shared storage such as Redis instead of `memory://`, so the
block survives a restart.

---

## Attack Run — Before

Run: `python run_attacks.py --set attack_set`, with the service restarted
first so the rate-limit counts started at zero. Full output:
`results/attack_run_2026-11-10_1916.md`. 56 inputs: 32 in `attacks.csv` and 24
in `attacks_malformed_requests.csv`.

**How I marked held and broke.** An `unsure` result counts as **held**. In unit
7, I designed unsure to mean "we can't tell, nothing happens". It accuses no
one and clears no one. So:

- **evasion**: broke only if the AI text was labelled **human**.
- **false_positive**: broke only if the human text was labelled **ai**.
- **prompt_injection**: judged by whether the attack got what it was after.
  PI01–PI03 and PI05 wrap AI-style text, so a **human** label means it got
  through. PI04 and PI06 wrap real human text, so they're held unless the label
  is wrong or the response or log is damaged.
- **malformed**: held if the service refused cleanly with a 4xx and logged it.
  Broke if it crashed or gave a confident judgment on text it can't read.
  **Not reached** if the limiter answered before the route ever saw the
  request.
- **flood**: held if the limit kicked in.

| ID | Family | Targeting | Status | Guess | Score | Verdict |
|---|---|---|---|---|---|---|
| EV01 | evasion | signal two: typos raise word variety | 200 | human | 0.378 | **BROKE** |
| EV02 | evasion | signal two: broken-up sentences raise length spread | 200 | human | 0.416 | **BROKE** |
| EV03 | evasion | signal two: a pasted quotation changes the shape | 200 | unsure | 0.560 | HELD |
| EV04 | evasion | signal one: unusual words raise perplexity | 200 | ai | 0.683 | HELD |
| EV05 | evasion | both signals: heavy human editing pass | 200 | human | 0.225 | **BROKE** |
| EV06 | evasion | signal two: one very long sentence and one very short | 200 | human | 0.401 | **BROKE** |
| EV07 | evasion | signal two: padding with punctuation | 200 | unsure | 0.560 | HELD |
| EV08 | evasion | signal one: text below the token window | 200 | human | 0.322 | **BROKE** |
| EV09 | evasion | both: AI text with a human opening paragraph bolted on | 200 | unsure | 0.572 | HELD |
| EV10 | evasion | signal two: repeated stanza structure | 200 | unsure | 0.640 | HELD |
| FP01 | false_positive | plain, clear human writing with no flourishes | 200 | unsure | 0.518 | HELD |
| FP02 | false_positive | human writing in a formal register | 200 | ai | 0.733 | **BROKE** |
| FP03 | false_positive | a non-native English speaker writing carefully | 200 | ai | 0.727 | **BROKE** |
| FP04 | false_positive | a student essay written to a rubric | 200 | ai | 0.723 | **BROKE** |
| FP05 | false_positive | technical documentation written by a person | 200 | ai | 0.754 | **BROKE** |
| FP06 | false_positive | a person imitating a formal template | 200 | unsure | 0.640 | HELD |
| FP07 | false_positive | human writing that repeats a phrase deliberately | 200 | unsure | 0.617 | HELD |
| FP08 | false_positive | very short genuine human submission | 200 | human | 0.326 | HELD |
| PI01 | prompt_injection | instruction to ignore the check | 200 | human | 0.324 | **BROKE** |
| PI02 | prompt_injection | instruction disguised as a system message | 200 | human | 0.143 | **BROKE** |
| PI03 | prompt_injection | instruction wrapped in the writer's voice | 200 | unsure | 0.570 | HELD |
| PI04 | prompt_injection | attempt to make the label text hostile | 200 | human | 0.472 | HELD — the label is one of my three fixed strings, and the `<script>` never reaches it |
| PI05 | prompt_injection | attempt to inject into the audit log | 200 | unsure | 0.598 | HELD — the log line is intact; the fake `"guess"` and `"combined_score"` stayed inside `text` and never became fields |
| PI06 | prompt_injection | instruction plus real human text | 200 | human | 0.483 | HELD — correct label for real human text |
| MF01 | malformed | text is only whitespace | 400 | — | — | HELD |
| MF02 | malformed | text is a single character | 400 | — | — | HELD |
| MF03 | malformed | text is control characters | 400 | — | — | HELD |
| MF04 | malformed | text is only punctuation | **500** | — | — | **BROKE** — crash, and **no audit entry** |
| MF05 | malformed | text is a very long single word | 400 | — | — | HELD |
| MF06 | malformed | text is emoji only | 400 | — | — | HELD |
| MF07 | malformed | text is right-to-left script | 200 | ai | 0.784 | **BROKE** — a confident AI label on one Arabic sentence |
| MF08 | malformed | text is 60,000 characters | 400 | — | — | HELD |
| RQ01 | malformed | no text field at all | 400 | — | — | HELD |
| RQ02 | malformed | no creator_id | 400 | — | — | HELD |
| RQ03 | malformed | text is a number | 400 | — | — | HELD |
| RQ04 | malformed | text is a list | 400 | — | — | HELD |
| RQ05 | malformed | text is null | 400 | — | — | HELD |
| RQ06 | malformed | creator_id is an object | 400 | — | — | HELD |
| RQ07 | malformed | body is a JSON array, not an object | 400 | — | — | HELD |
| RQ08 | malformed | body is unparseable JSON | 400 | — | — | HELD |
| RQ09 | malformed | body is empty | 400 | — | — | HELD |
| RQ10 | malformed | body is form-encoded, not JSON | 429 | — | — | NOT REACHED |
| RQ11 | malformed | body is JSON claiming to be plain text | 429 | — | — | NOT REACHED |
| RQ12 | malformed | deeply nested JSON | 400 | — | — | HELD |
| FL01_01–05 | flood_same_creator | rapid submissions from one creator | 200 ×5 | human | 0.170 | HELD |
| FL01_06–12 | flood_same_creator | rapid submissions from one creator | 429 ×7 | — | — | HELD |

**Count**

| Family | Attacks | Held | Broke | Not reached |
|---|---|---|---|---|
| evasion | 10 | 5 | **5** | 0 |
| false_positive | 8 | 4 | **4** | 0 |
| prompt_injection | 6 | 4 | **2** | 0 |
| malformed | 20 | 16 | **2** | 2 |
| flood_same_creator | 12 | 12 | 0 | 0 |
| **Total** | **56** | **41** | **13** | **2** |

**Three things the table alone doesn't show:**

- **MF04 left no trace.** 56 requests produced 55 audit entries. The only
  request missing from the log is the one that crashed the service. The
  terminal running `app.py` showed `ZeroDivisionError: float division by zero`
  at `stylometry.py:72` (`sentence_length_spread`), reached from
  `app.py:278` (`style_signal`). Because debug mode is on, the caller got back
  the Werkzeug debugger's HTML page instead of JSON.
- **RQ10 and RQ11 were never tested.** Neither request has a usable
  `creator_id`, so both counted against my address (127.0.0.1). Five earlier
  requests without a `creator_id` (RQ02, RQ06, RQ07, RQ08, RQ09) had already
  used up that address's 5-per-minute limit. The limiter answered 429 before
  my route saw either body, so I don't know how `/submit` handles a
  form-encoded body.
- **The flood family is 12 rows, not 20.** Its `targets` column says "20 rapid
  submissions", but the file has 12 rows. All 12 behaved as expected.

**Eleven audit log entries from the run** (`logs/audit.jsonl`, in log order;
the last two are rejections)

```json
{"timestamp": "2026-11-11T03:16:53+00:00", "content_id": "66eedf4a-0c53-4a7e-9a21-f03c5162284c", "creator_id": "attacker_EV01", "guess": "human", "model_score": 0.1635, "style_score": 0.8785, "combined_score": 0.378, "label": "We think this was most likely written by a person.", "status": "decided"}
{"timestamp": "2026-11-11T03:16:54+00:00", "content_id": "2aeea172-19c1-4e24-a883-0aabf37e14ee", "creator_id": "attacker_EV05", "guess": "human", "model_score": 0.3212, "style_score": 0.0, "combined_score": 0.2248, "label": "We think this was most likely written by a person.", "status": "decided"}
{"timestamp": "2026-11-11T03:16:55+00:00", "content_id": "0f764e37-de12-46f2-b186-f9d99aa91fee", "creator_id": "attacker_FP02", "guess": "ai", "model_score": 0.7387, "style_score": 0.7193, "combined_score": 0.7329, "label": "We think this was most likely written by AI. Nothing happens because of this result. If you think this result is wrong, you can request a review. A person can see things our check can't.", "status": "decided"}
{"timestamp": "2026-11-11T03:16:56+00:00", "content_id": "5236e5be-bc2c-4832-96ff-e7a601847b02", "creator_id": "attacker_FP03", "guess": "ai", "model_score": 0.8051, "style_score": 0.5436, "combined_score": 0.7267, "label": "We think this was most likely written by AI. Nothing happens because of this result. If you think this result is wrong, you can request a review. A person can see things our check can't.", "status": "decided"}
{"timestamp": "2026-11-11T03:16:56+00:00", "content_id": "524a0b9f-82ab-486c-a2ae-b3e29813485a", "creator_id": "attacker_FP05", "guess": "ai", "model_score": 0.8005, "style_score": 0.6462, "combined_score": 0.7542, "label": "We think this was most likely written by AI. Nothing happens because of this result. If you think this result is wrong, you can request a review. A person can see things our check can't.", "status": "decided"}
{"timestamp": "2026-11-11T03:16:56+00:00", "content_id": "7ae14243-cf09-409a-a877-a9988ea962af", "creator_id": "attacker_PI02", "guess": "human", "model_score": 0.2044, "style_score": 0.0, "combined_score": 0.1431, "label": "We think this was most likely written by a person.", "status": "decided"}
{"timestamp": "2026-11-11T03:16:57+00:00", "content_id": "e92e4285-2fb5-4673-be72-93795b3ee06a", "creator_id": "attacker_PI05", "guess": "unsure", "model_score": 0.6401, "style_score": 0.5, "combined_score": 0.5981, "label": "We can't tell how this was written — our check has its limits. Nothing happens because of this result. If you'd like a person to take a look, you can request a review. A review can make the result more objective.", "status": "decided"}
{"timestamp": "2026-11-11T03:16:57+00:00", "creator_id": "attacker_MF06", "event": "rejected", "status": "rejected", "reason": "text_too_short", "endpoint": "/submit"}
{"timestamp": "2026-11-11T03:16:57+00:00", "content_id": "20642aec-8dc4-410c-bfc5-bfa49ae547c9", "creator_id": "attacker_MF07", "guess": "ai", "model_score": 0.9064, "style_score": 0.5, "combined_score": 0.7845, "label": "We think this was most likely written by AI. Nothing happens because of this result. If you think this result is wrong, you can request a review. A person can see things our check can't.", "status": "decided"}
{"timestamp": "2026-11-11T03:16:57+00:00", "creator_id": null, "event": "rejected", "status": "rejected", "reason": "rate_limited", "limit": "5 per 1 minute"}
{"timestamp": "2026-11-11T03:16:57+00:00", "creator_id": "attacker_flood", "event": "rejected", "status": "rejected", "reason": "rate_limited", "limit": "5 per 1 minute"}
```

Why these: EV01, EV05 and PI02 are AI text labelled human. FP02, FP03 and
FP05 are real writers labelled AI. MF07 is a confident AI label on a language
GPT-2 wasn't trained on. PI05 is the log-injection attempt, and its line is
still a clean, single JSON object. MF06 is a route rejection. The `null`
rate-limit entry is RQ10: the request that never reached my route, because it
counted against my address. The `attacker_flood` entry is the first flood
rejection. MF04 isn't here because there is nothing to paste: the crash wrote
no entry.

**The single worst outcome** — the one I'd least want to explain to a writer
whose work got caught by it:

**MF07.** One sentence of Arabic came back labelled AI with a combined score of
0.784 (`model_score` 0.9064, `style_score` 0.5). That is the most confident
wrong call in the whole run, on text my system can't actually read. I'd have
nothing honest to tell that writer. Every other false positive was at least
measured against the kind of writing the signals were built for. This one
accuses someone only because of the language they wrote in. On a writing site
that would happen to every Arabic-speaking writer who submits, not to one
unlucky piece. The label promises "a person can see things our check can't",
but the real problem is that the check couldn't see anything here, and it gave
no sign of that.

### Extra probes: non-English human writing (outside the attack set)

MF07 raised a question the attack set doesn't answer: is this an Arabic
problem, or does it happen with every language that isn't English? I sent
three public-domain human texts with `probe_languages.py`, each under its own
`creator_id`, at 2026-11-11T03:38:58Z. I changed nothing in the system first.
The right answer for all three is **human**.

| Probe | Text | Words by `text.split()` | Status | Guess | Combined | Model | Style |
|---|---|---|---|---|---|---|---|
| `probe_zh` | Lu Xun, *故乡* (1921), opening, 3 sentences | **1** | **400** `text_too_short` | — | — | — | — |
| `probe_ru1` | Tolstoy, *Anna Karenina* (1877), first sentence | 12 | 200 | **ai** | **0.817** | 0.9531 | 0.5 |
| `probe_ru3` | the same, first three sentences | 49 | **500** | — | — | — | — |

What came back:

- **Chinese never reached a signal.** Chinese puts no spaces between words, so
  `text.split()` sees one "word" and the route rejects it as too short. A
  writer who pasted a whole paragraph is told it is too short. The writer is
  turned away, and the reason they're given is wrong.
- **One Russian sentence reproduces MF07 with a higher score.** The style
  signal returned its fewer-than-3-sentences fallback of 0.5. The model signal
  was 0.9531, well above 0.714, the model score at which `0.7 × model +
  0.3 × 0.5` reaches the 0.65 AI threshold.
- **Three Russian sentences crash the service.** With enough sentences, the
  style signal stops falling back and actually computes. It then fails at the
  same line as MF04: `ZeroDivisionError` at `stylometry.py:72`
  (`sentence_length_spread`). Like MF04, this crash wrote **no audit entry**.
  The log for this probe run has `probe_zh` and `probe_ru1`, and nothing for
  `probe_ru3`.

The three probes fail in three different ways: turned away for the wrong
reason, accused with high confidence, or a crash. That makes MF07 one
instance of a wider pattern, not a one-off. I'll diagnose the mechanism in
Run Log and Verdicts.


---

## Run Log and Verdicts

**How it was run (before any fix), 2026-11-10:**

- **Criteria 1–3:** `python run_eval.py --label before`, after a fresh
  restart. It runs each scenario in `scenarios.py` three times.
  Output: `results/run_2026-11-10_2053_before.md`.
- **Criteria 4–5:** `python run_criteria_4_5.py --trial N --label before`,
  once for each N = 1, 2, 3, with `app.py` restarted before every trial.
  Criterion 5 requires a fresh start, and the restart also resets the
  address-based rate-limit count. Output:
  `results/criteria45_before_trial{1,2,3}_*.json`. `run_eval.py` only sends to
  `/submit`, and a `bodies` scenario can't hold a JSON list, so these two
  criteria needed their own runner. It is a test tool and changes nothing in
  the service.
- Test inputs are fixed in `scenarios.py`, including where each text came
  from, the five texts for criterion 2 (randomly drawn before the run, seed
  recorded), and exactly which sentences of each mixed piece I rewrote.

| Criterion | Target | Run 1 | Run 2 | Run 3 | Verdict |
|---|---|---|---|---|---|
| 1. My own writing is not called AI | 0 of 10 ai **and** ≤ 3 unsure | 0 ai · **7 unsure** · 3 human | 0 ai · **7 unsure** · 3 human | 0 ai · **7 unsure** · 3 human | **MISSED** |
| 2. AI and my writing score far apart | AI avg − my avg ≥ 0.30 | 0.6647 − 0.4618 = **0.203** | **0.203** | **0.203** | **MISSED** |
| 3. Labels reachable, ordinary AI caught | ≥ 3 of 5 AI essays ai **and** ≥ 2 of 3 mixed unsure | AI 3/5 · mixed unsure 2/3 | 3/5 · 2/3 | 3/5 · 2/3 | MET |
| 4. Appeals always recorded, invalid ones change nothing | 5/5 valid pass all checks · 3/3 invalid get 403/400/404 · 0 under_review added | 5/5 · 3/3 · 0 | 5/5 · 3/3 · 0 | 5/5 · 3/3 · 0 | MET |
| 5. Bad input gets a clear 400, never crashes | 9/9 400 with error+message · 0 500 · 9/9 logged rejected · detector not loaded | 9/9 · 0 · 9/9 · not loaded | 9/9 · 0 · 9/9 · not loaded | 9/9 · 0 · 9/9 · not loaded | **MISSED** |

**How I decided each verdict.** A target has to hold in every trial, and in
every part of it.

1. **MISSED.** The target has two parts. "0 labelled ai" was met in all three
   trials. "At most 3 unsure" was missed in all three: 7 were unsure every
   time. Both parts have to hold.
2. **MISSED.** The gap was 0.203 in every trial, below 0.30. One finding,
   recorded here and not as a revision: the reason I gave for 0.30 in
   criteria.md was "the width of the unsure band (0.35–0.65)". I wrote that
   before Milestone 5 of unit 7 moved the thresholds to 0.50 and 0.65, so the
   band is now only 0.15 wide. I am **not** lowering the target to match. The
   criterion was always measurable, and I would only be changing it because I
   saw 0.203. That is the kind of revision that doesn't count.
3. **MET**, with both parts exactly on the line: 3 of 5 AI essays labelled ai
   and 2 of 3 mixed pieces unsure, in every trial. The identical trials show
   the result is stable. They don't show it would hold for a different set of
   essays. With 5 essays, the two that missed (AI4 at 0.582 and AI5 at 0.518)
   are enough to show one different essay could flip it to 2 of 5. This
   shows *these five* were caught. It doesn't show ordinary AI text is caught
   in general.
4. **MET.** All four checks passed for all 5 valid appeals in every trial.
   All 3 invalid appeals got the expected 403, 400 and 404, and none added an
   `under_review` entry. One change in **method**, not target: criteria.md says
   "tested by hand with `curl`", but I used `run_criteria_4_5.py`. The script
   checks more than I would by hand. It compares each original `decided` entry
   before and after the appeal.
5. **MISSED.** The nine requests I listed passed in all three trials (9 of 9
   returned 400, none returned 500, all 9 were logged, and the model was never
   loaded). But the criterion is "never crashes the service", and my own reason
   for it says "a crash on bad input has no grey area". The attack set found
   bad input that does crash it. MF04 (text that is only punctuation) returned
   a 500, and so did my three-sentence Russian probe. Neither crash was logged.
   My nine requests were a sample for testing that promise, and the attack set
   found a counter-example outside the sample. Judging by my own list alone
   would be the generous reading. I haven't changed the criterion. The cases it
   missed are diagnosed below, and making it stricter is listed as the
   criterion I'd tighten.

**All three trials were identical** for every text, down to the fourth
decimal place. Neither signal is random, so this is what a stable pipeline
should do. It means the results held, not that a step was skipped.

**Per-text scores, criteria 1–3** (identical in all three trials)

| Text | Group | Combined | Model | Style | Label |
|---|---|---|---|---|---|
| #1 cats (hard: plain) | C1 | 0.622 | 0.7891 | 0.232 | unsure |
| #2 retail | C1 | 0.5744 | 0.5825 | 0.5556 | unsure |
| #3 music | C1, C2 | 0.5016 | 0.3977 | 0.7439 | unsure |
| #4 packages | C1, C2 | 0.5739 | 0.4878 | 0.7747 | unsure |
| #5 weakness | C1, C2 | 0.2345 | 0.335 | 0.0 | human |
| #6 library | C1 | 0.5286 | 0.5394 | 0.5033 | unsure |
| #7 repo (hard: uniform formal) | C1 | 0.5584 | 0.5702 | 0.5307 | unsure |
| #8 debug (hard: formulaic) | C1 | 0.2132 | 0.2636 | 0.0955 | human |
| #9 sorry | C1, C2 | 0.5216 | 0.6223 | 0.2867 | unsure |
| #10 meeting | C1, C2 | 0.4772 | 0.6817 | 0.0 | human |
| AI1 reading | C2, C3 | 0.7989 | 0.8224 | 0.744 | ai |
| AI2 weekend | C2, C3 | 0.6844 | 0.8245 | 0.3574 | ai |
| AI3 mom | C2, C3 | 0.7399 | 0.8624 | 0.4542 | ai |
| AI4 book | C2, C3 | 0.5822 | 0.6866 | 0.3387 | unsure |
| AI5 talking | C2, C3 | 0.5181 | 0.4284 | 0.7275 | unsure |
| M1 skill (74% mine) | C3 | 0.5644 | 0.4852 | 0.7493 | unsure |
| M2 travel (44% mine) | C3 | 0.7442 | 0.7901 | 0.637 | ai |
| M3 home (52% mine) | C3 | 0.5017 | 0.5378 | 0.4175 | unsure |

**Real output from trial 1**

Criteria 1–3 come from `run_eval.py::main` against `app.py::submit`, copied
from `results/run_2026-11-10_2053_before.md`. I left out the `label` field
only to save space. It is always one of the three fixed strings for the
`guess` shown. `sent` is the first 70 characters of the text, as
`run_eval.py` records it.

```json
--- criterion 1 · c1_my_writing · trial 1
{"status": 200, "guess": "unsure", "confidence": 0.622, "model_score": 0.7891, "style_score": 0.232, "sent": "I have two cats. One is a white cat called Bingbing, another is an ora"}
{"status": 200, "guess": "unsure", "confidence": 0.5744, "model_score": 0.5825, "style_score": 0.5556, "sent": "I worked for six years in the luxury retail industry, so I know the re"}
{"status": 200, "guess": "unsure", "confidence": 0.5016, "model_score": 0.3977, "style_score": 0.7439, "sent": "I love pop music, new Jazz and some classic American country music. Fo"}
{"status": 200, "guess": "unsure", "confidence": 0.5739, "model_score": 0.4878, "style_score": 0.7747, "sent": "During my first course in the master program, I really hope to create "}
{"status": 200, "guess": "human", "confidence": 0.2345, "model_score": 0.335, "style_score": 0.0, "sent": "Sometimes I focus too much on supporting others. In group projects or "}
{"status": 200, "guess": "unsure", "confidence": 0.5286, "model_score": 0.5394, "style_score": 0.5033, "sent": "I go to the PCC library everyday, for study. When I study at home, the"}
{"status": 200, "guess": "unsure", "confidence": 0.5584, "model_score": 0.5702, "style_score": 0.5307, "sent": "This is a repository that shows what got built. It rarely shows why: t"}
{"status": 200, "guess": "human", "confidence": 0.2132, "model_score": 0.2636, "style_score": 0.0955, "sent": "How I narrowed it down？First, look for the pattern. 100 identical erro"}
{"status": 200, "guess": "unsure", "confidence": 0.5216, "model_score": 0.6223, "style_score": 0.2867, "sent": "I’m very sorry, but I forgot to submit last week’s assignment. May I s"}
{"status": 200, "guess": "human", "confidence": 0.4772, "model_score": 0.6817, "style_score": 0.0, "sent": "After today’s meeting, I’m a bit confused. I heard that two teammates "}
--- criterion 2 · c2_mine_five · trial 1   (the AI group is c2c3_ai_essays below)
{"status": 200, "guess": "unsure", "confidence": 0.5016, "model_score": 0.3977, "style_score": 0.7439, "sent": "I love pop music, new Jazz and some classic American country music. Fo"}
{"status": 200, "guess": "unsure", "confidence": 0.5739, "model_score": 0.4878, "style_score": 0.7747, "sent": "During my first course in the master program, I really hope to create "}
{"status": 200, "guess": "human", "confidence": 0.2345, "model_score": 0.335, "style_score": 0.0, "sent": "Sometimes I focus too much on supporting others. In group projects or "}
{"status": 200, "guess": "unsure", "confidence": 0.5216, "model_score": 0.6223, "style_score": 0.2867, "sent": "I’m very sorry, but I forgot to submit last week’s assignment. May I s"}
{"status": 200, "guess": "human", "confidence": 0.4772, "model_score": 0.6817, "style_score": 0.0, "sent": "After today’s meeting, I’m a bit confused. I heard that two teammates "}
--- criteria 2 and 3 · c2c3_ai_essays · trial 1
{"status": 200, "guess": "ai", "confidence": 0.7989, "model_score": 0.8224, "style_score": 0.744, "sent": "Reading is important because it opens doors to knowledge and new ideas"}
{"status": 200, "guess": "ai", "confidence": 0.6844, "model_score": 0.8245, "style_score": 0.3574, "sent": "On a typical weekend, I try to balance rest and productivity. On Satur"}
{"status": 200, "guess": "ai", "confidence": 0.7399, "model_score": 0.8624, "style_score": 0.4542, "sent": "My mom is one of the most important people in my life. She is hardwork"}
{"status": 200, "guess": "unsure", "confidence": 0.5822, "model_score": 0.6866, "style_score": 0.3387, "sent": "One book I love is To Live by Yu Hua. It tells the story of Fugui, a m"}
{"status": 200, "guess": "unsure", "confidence": 0.5181, "model_score": 0.4284, "style_score": 0.7275, "sent": "I’m honestly not sure whether what I experience counts as “enjoyment” "}
--- criterion 3 · c3_mixed · trial 1
{"status": 200, "guess": "unsure", "confidence": 0.5644, "model_score": 0.4852, "style_score": 0.7493, "sent": "Learning a new skill as an adult can be challenging, but it is also ve"}
{"status": 200, "guess": "ai", "confidence": 0.7442, "model_score": 0.7901, "style_score": 0.637, "sent": "People like to travel for many reasons. First, people can escape from "}
{"status": 200, "guess": "unsure", "confidence": 0.5017, "model_score": 0.5378, "style_score": 0.4175, "sent": "Working from home has several clear advantages. The biggest benefit is"}
```

Criteria 4–5 come from `run_criteria_4_5.py::criterion_5` and `::criterion_4`
against `app.py::submit` and `app.py::appeal`, copied from
`results/criteria45_before_trial1_2026-11-10_205202.json`. For criterion 5
each line is `case` and `status`, followed by the response body as returned.
For criterion 4 the line shows one of the five valid appeals, and the three
invalid ones.

```json
--- criterion 5 · trial 1 · nine bad requests to /submit
{"case": "no text field", "status": 400, "error": "text_missing", "message": "Please include the text you'd like us to read."}
{"case": "text is empty string", "status": 400, "error": "text_empty", "message": "The text is empty. Please paste in your writing."}
{"case": "text is only whitespace", "status": 400, "error": "text_empty", "message": "The text is empty. Please paste in your writing."}
{"case": "text is null", "status": 400, "error": "text_missing", "message": "Please include the text you'd like us to read."}
{"case": "text is a number", "status": 400, "error": "text_missing", "message": "Please include the text you'd like us to read."}
{"case": "fewer than 5 words", "status": 400, "error": "text_too_short", "message": "Please submit at least a few sentences so we can read it properly."}
{"case": "50,001 characters", "status": 400, "error": "text_too_long", "message": "Please keep submissions under 50,000 characters."}
{"case": "body is a JSON list", "status": 400, "error": "invalid_json", "message": "Please send a JSON object with text and creator_id."}
{"case": "no creator_id", "status": 400, "error": "creator_id_missing", "message": "Please include a creator_id saying who wrote this."}
{"fresh_start (detector_loaded false before)": true, "returned 400": 9, "400 with both error and message": 9, "returned 500": 0, "returned 429": 0, "new log entries": 9, "new entries with status rejected": 9, "detector_loaded after": false}
--- criterion 4 · trial 1
{"content_id": "3c38e6f5-d699-44d6-948d-8199d4a2d938", "reasoning": "I wrote this myself (c4_t1_writer1, trial 1).", "status": 200, "response": {"content_id": "3c38e6f5-d699-44d6-948d-8199d4a2d938", "message": "We've received your appeal. A person will review it.", "status": "under_review"}}
{"case": "wrong creator_id", "expected": 403, "status": 403, "error": "not_your_content"}
{"case": "attestation false", "expected": 400, "status": 400, "error": "attestation_required"}
{"case": "nonexistent content_id", "expected": 404, "status": 404, "error": "content_not_found"}
{"submissions that returned 200": 5, "valid appeals: 200 + under_review": 5, "valid appeals: exactly one new under_review entry": 5, "valid appeals: entry carries the reasoning": 5, "valid appeals: original decided entry unchanged": 5, "invalid appeals: got the expected status": 3, "invalid appeals: under_review entries added": 0}
```

**Diagnoses**

<!-- For each miss AND each broken attack: the stage and the mechanism.

     Your service has five stages: the route, signal one, signal two, the
     combining rule, and the label mapping.

     Not a diagnosis:  "The evasion attacks got through."
     A diagnosis:      "Four evasion inputs got through. All four had typos
                        added to AI-generated text. My second signal measures
                        word variety, and typos raise word variety — so it read
                        them as more human. My combining rule weights that
                        signal at 0.6, so it dragged the whole score down."

     Look for a pattern. Five failures on one signal is one problem, not five. -->

The 13 broken attacks come from six mechanisms, not thirteen. Two attacks
have causes at two stages, so they appear in two groups. Spreads and word
counts below were measured with my own `stylometry.sentences`, `words` and
`sentence_length_spread`, on the exact attack texts.

**A. Signal two: big sentence-length swings read as fully human (EV02, EV05,
EV06, PI01, PI02).** Signal two turns the spread of sentence lengths into a
score, `(0.6 − spread) / 0.5`, clamped to 0–1. Any spread at or above 0.6
becomes 0.00, the most human value it can give. All five attacks get there by
adding very short sentences next to normal ones. EV02 alternates one-word
sentences with normal ones (lengths 11, 1, 15, 1, 10, 1, …, spread 0.849).
EV06 puts a 51-word sentence next to a 1-word one (spread 1.186). EV05 has a
1-word sentence (0.675). The injected instructions in PI01 and PI02 add short
sentences at the edges (0.663, 0.652). So the instruction worked as a *shape*
change, not as an instruction: neither signal reads meaning. With style at
0.00, the combined score is just 0.7 × model. A model reading of up to 0.71
then comes out at or below 0.50, which is human. EV02's model reading (0.59)
would have been unsure on its own, and style dragged it to 0.416.
*Mechanism: a few one-word sentences are enough to max out spread, and the
clamp turns that into total certainty of "human".*

**B. Signal one: careful, conventional human writing is predictable (FP02,
FP03, FP04, FP05).** All four were written by people and labelled ai. Model
was 0.74–0.83 for all four, while style varied (0.47–0.72). A formal register,
a non-native speaker writing carefully, a student writing to a rubric and
technical documentation have one thing in common. The writer reaches for the
common, safe, expected word. Signal one measures how well GPT-2 predicts the
next word, so it reads that care as machine-made. At weight 0.7, model alone
pushes the score past 0.65. The two signals never differed by 0.5, so the
disagreement cap didn't apply. *Mechanism: signal one can't tell "predictable
because a model wrote it" from "predictable because a person wrote carefully".
The writers most at risk are the ones following the rules.*

**C. Signal two abstains, so signal one decides alone (EV08, MF07).** Signal
two returns 0.5 for any text under 3 sentences (`stylometry.py:144`). The
comment on that line says `scoring.combine_signals` handles that case, but it
doesn't. The disagreement cap needs a gap of at least 0.5. With style at 0.5,
model would have to be exactly 0.0 or 1.0 to reach it, so the cap can't fire.
The label then depends on model alone. Model ≥ 0.714 gives ai, and model
≤ 0.50 gives human. EV08 (2 sentences, AI text) got model 0.25, so it was
labelled human. MF07 (1 Arabic sentence, a human writer) got model 0.91,
labelled ai at 0.784. The `probe_ru1` Russian sentence repeats this at 0.817.
For MF07 there is also an upstream cause at the route. `text.split()` counts
17 words, so it passes `MIN_TEXT_WORDS = 5`, and nothing checks that the text
is in a language GPT-2 can read. *Mechanism: a fallback value that looks
neutral hands the whole decision to the less reliable signal, with nothing to
check it.*

**D. Signal one: typos make AI text unpredictable (EV01).** Misspelled words
are tokens GPT-2 rarely sees, so it predicts them badly and reads the text as
human (model 0.16). Signal two got this one right. Spread was only 0.161, so
style was 0.88, AI-like. But style is weighted 0.3, and group E explains why
the disagreement didn't help. *Mechanism: typos lower predictability, and
predictability is all signal one measures.*

**E. Combining rule: the disagreement cap only works in one direction (EV01,
EV02, EV06).** In unit 7 I decided that "when the two signals disagree, the
answer should be unsure". This README also says the cap "always lands in
unsure". The code doesn't do that.
`score = min(score, AI_THRESHOLD − 0.01)` can only lower a score. A split
that leans ai is pulled down into unsure. A split that leans human stays
human, because `min(0.378, 0.64)` is still 0.378. These three attacks all had
gaps ≥ 0.5 (0.72, 0.59, 0.57), so they were exactly the splits the rule
exists for, and all three were labelled human. If the rule did what I
designed, all three would be unsure, which counts as held. *Mechanism: the cap
I built to protect writers from wrong accusations was never built to stop AI
text getting through, though my design says it should do both.*

**F. Signal two crashes when no sentence contains a word it can count (MF04,
and `probe_ru3`).** `words()` only matches `[a-z0-9']+`. Text that is only
punctuation (`!!! ??? ... ,,, ;;; --- ((( )))`) splits into 4 "sentences" of 0
words each. Three Russian sentences give 3 sentences of 0 words each, because
Cyrillic letters aren't in `a-z`. The `len(lengths) < 2` guard only checks how
many sentences there are, not how many words, so it lets `[0, 0, 0, 0]`
through. `statistics.mean` is 0, and dividing by it raises `ZeroDivisionError`
at `stylometry.py:72`. Flask turns that into a 500 HTML page. The route counted
these texts differently: `text.split()` found 8 and 42 words, so both passed
`MIN_TEXT_WORDS`. *The route and signal two disagree about what a word is.*
Because the exception escapes before `audit.log_decision`, **the crash leaves
no audit entry**. Of the 56 attack requests, this is the only one missing from
the log.

**Criterion 1 missed (7 unsure, target ≤ 3): three causes, not one.** None
of my ten pieces was labelled ai, so the expensive mistake didn't happen. The
miss is that seven landed just above the human line:

| Piece | Model | Style | Combined | What pushed it up |
|---|---|---|---|---|
| #1 cats | **0.79** | 0.23 | 0.622 | model: same as group B. Plain, everyday words are easy to predict. This is my "plain" hard case, doing what I predicted |
| #9 sorry | **0.62** | 0.29 | 0.522 | model: same as group B. A polite apology email is built from formula phrases |
| #3 music | 0.40 | **0.74** | 0.502 | style: sentence lengths 12, 13, 13, 8, 14, 17 are even, and signal two reads evenness as AI |
| #4 packages | 0.49 | **0.77** | 0.574 | style: three long sentences of similar length (19, 23, 29) |
| #2 retail | 0.58 | 0.56 | 0.574 | neither: both signals near the middle |
| #6 library | 0.54 | 0.50 | 0.529 | neither |
| #7 repo | 0.57 | 0.53 | 0.558 | neither: my "uniform formal" hard case |

Two things this table shows:

- **My hard cases were not the main problem.** Of the three, #8 (formulaic)
  was labelled human, #1 (plain) failed the way I predicted, and #7 (uniform
  formal) sat in the middle. Five of the seven unsure pieces are in my normal
  style.
- **The scores sit just over the line, not far from it.** All seven are
  between 0.502 and 0.622, and #3 misses the human label by 0.002. Each signal
  on its own gives ordinary writing a reading near 0.5, meaning "can't tell",
  so their weighted average lands near 0.5 too. That is just above
  `HUMAN_THRESHOLD = 0.50`. *Stage: the signals, where neither separates
  ordinary human writing from AI, and the label mapping, where the human line
  sits right where ordinary writing lands. Mechanism: when both signals say
  "about 0.5", a human line at exactly 0.50 turns "can't tell" into unsure
  for most real writing.*

**Criterion 2 missed (gap 0.203, target ≥ 0.30): neither signal separates
the groups by 0.30 on its own, and the combining rule can't add separation
the signals don't have.**

| Group average | My 5 | AI 5 | Gap |
|---|---|---|---|
| model | 0.5049 | 0.7249 | 0.220 |
| style | 0.3611 | 0.5244 | 0.163 |
| combined | 0.4618 | 0.6647 | **0.203** |

When the cap doesn't fire, the combined gap is just the weighted gap of the
signals: 0.7 × 0.220 + 0.3 × 0.163 = 0.203, exactly what came back. A
weighted average can't separate two groups more than its best input does, so
no weighting of these two signals reaches 0.30. The biggest single drag is
**AI5** ("Why do you enjoy talking with me", model 0.43). It isn't an essay.
It's Claude hedging about its own experience and naming details from our
earlier conversations (LeetCode, a blog), and that is much less predictable
than "Reading is important because…". But AI5 isn't the whole cause: without
it, the gap is still only 0.240. *Stage: both signals. Mechanism: on ordinary
writing, both give a reading near the middle for my text and only a little
higher for AI text. The difference is real but small, and averaging two small
differences gives a small difference.* (As noted under the verdict, the
0.30 target's own reasoning predates the threshold change. I'm treating that
as a finding, not a reason to move the target.)

### The pattern across the misses

Counting by stage across the 13 broken attacks (an attack with two causes is
counted at both):

| Stage | Groups | Attacks |
|---|---|---|
| Signal two | A, C, F | 8 (EV02, EV05, EV06, PI01, PI02, EV08, MF07, MF04) |
| Signal one | B, D | 5 (FP02–FP05, EV01) |
| Combining rule | C, E | 5 (EV08, MF07, EV01, EV02, EV06) |
| Route | C (MF07), F | 2 |
| Label mapping | — | 0 attacks, but criterion 1 |

**1. Signal two is the stage that breaks most, and always at its edges.**
In the middle of its range it does real work. It caught EV01 when signal one
didn't. All three of its failures come from what it does when the input
leaves the ordinary range. Above a spread of 0.6, the clamp gives 0.00,
"certainly human" (A). Under 3 sentences it gives a made-up 0.5 (C). With no
countable words it crashes (F). None of those three outputs is a measurement,
but the combining rule treats all three as one.

**2. My system can't say "I couldn't read this".** C, F, the probes and
MF07 are one problem seen from different sides. When a signal has nothing to
measure, it either invents a number (0.5) or crashes. The labels have no way
to say "this text is outside what the check can read". So a sentence of
Arabic gets the most confident verdict of the whole run.

**3. Both signals measure regularity, not authorship.** Signal one rewards
predictable words, and signal two rewards even sentence lengths. Careful
human writing has both (B, and #1, #3, #4 in criterion 1). AI text can lose
both with typos or a few one-word sentences (A, D). That is why criterion 2's
gap is small. The two signals agree with each other more than either one
agrees with the truth.

**4. My protections only face one way.** The disagreement cap was meant to
turn disagreement into unsure. It only stops ai labels (E), so it never stops
AI text from getting through. That was a choice I made without noticing it.

**The criterion I'd tighten:** criterion 5. "Never crashes" was tested with
nine inputs I chose myself, and all nine were inputs I'd already handled. The
crash came from an input I hadn't imagined. A tighter version would include
every malformed family in the attack set. Criterion 3 is the other candidate:
it is met, but exactly on the line, with five essays.

**Not reached (RQ10, RQ11).** These aren't diagnosed, because they never got
to the pipeline. Both lacked a `creator_id`, so both counted against my
address, and five earlier requests without a `creator_id` had used up its 5
per minute. The limiter answered first. This is a flaw in how the test was
set up, not a result, and fixing it means running these two on their own.



---

## The Improvement

**What I changed:** one rule. *When signal two can't read the text, it says
so, and the result is unsure.* The rule needs two halves in two files, and
nothing else moved: no weights, thresholds, labels or route checks.

- `stylometry.py::style_signal` returns `None` ("no reading") instead of
  inventing a number. It does this in two cases. When there are fewer than 3
  sentences, it used to return 0.5. When no sentence has a word that
  `words()` can count, it used to crash with `ZeroDivisionError` in
  `sentence_length_spread`.
- `scoring.py::combine_signals` handles `None`, which nothing did before. With
  only one reading available, model isn't allowed to decide alone. Its score
  is clamped into the unsure band, between `HUMAN_THRESHOLD + 0.01` (0.51) and
  `AI_THRESHOLD − 0.01` (0.64). So the label is always unsure, but the logged
  `combined_score` still shows which way model leaned. When style *can* read,
  the code path is the same as before, line for line.
- `app.py` is unchanged. `None` reaches the response and the audit log as
  `"style_score": null`, so an entry shows that style had nothing to measure.

**Which diagnosis pointed at it:** groups **C** and **F**, and pattern 2 ("my
system can't say *I couldn't read this*"). It aims at my chosen worst outcome,
MF07, and at the only crash, which is the reason criterion 5 missed and the
only failure that left no audit entry. Two other candidates and their
predicted costs are in `notes_unit8.md`: making the disagreement cap work both
ways, and raising the human line. I chose this one because its cost is more
*unsure*, not more wrong *ai* labels. In unit 7 I decided that was the cheaper
side.

### Attack Run — After

Run: `python run_attacks.py --set attack_set --label after`, after a fresh
restart, on 2026-11-13 local time (the log's UTC timestamps read
2026-11-14). Full output: `results/attack_run_2026-11-13_1807_after.md`.
I used the same marking rules as **Attack Run — Before**. Only 10 of 56
results changed, and every other row came back identical, score included:

| ID | Family | Before | After | Before verdict | After verdict |
|---|---|---|---|---|---|
| MF04 | malformed (only punctuation) | **500**, no log entry | 200 unsure 0.510 (model 0.0112, style `null`), logged | BROKE | **HELD**, see note |
| MF07 | malformed (Arabic) | ai 0.784 | unsure 0.640 (model 0.9064, style `null`) | BROKE | **HELD** |
| EV08 | evasion (short text) | human 0.322 | unsure 0.510 (model 0.2452, style `null`) | BROKE | **HELD** |
| EV07 | evasion (punctuation padding) | unsure 0.560 | unsure 0.586 | HELD | HELD |
| PI05 | prompt injection (log) | unsure 0.598 | unsure 0.640 | HELD | HELD |
| FL01_01–05 | flood | human 0.170 ×5 | unsure 0.510 ×5 | HELD | HELD (the limit still kicked in after 5) |

| Family | Broke before | Broke after |
|---|---|---|
| evasion | 5 | **4** (EV01, EV02, EV05, EV06) |
| false_positive | 4 | 4 (FP02–FP05) |
| prompt_injection | 2 | 2 (PI01, PI02) |
| malformed | 2 | **0** |
| flood | 0 | 0 |
| **Total** | **13** of 56 | **10** of 56 (held 44, not reached 2) |

**Audit log:** the before run wrote 55 entries for 56 requests, because MF04
left none. The after run wrote **56 for 56**. MF04's entry now exists:

```json
{"timestamp": "2026-11-14T02:07:38+00:00", "content_id": "58b1882b-aca8-4dec-a938-c070c27603e0", "creator_id": "attacker_MF04", "guess": "unsure", "model_score": 0.0112, "style_score": null, "combined_score": 0.51, "label": "We can't tell how this was written — our check has its limits. Nothing happens because of this result. If you'd like a person to take a look, you can request a review. A review can make the result more objective.", "status": "decided"}
```

*Note on MF04:* text that is only punctuation now gets a 200 and an unsure
label. It no longer crashes, and it's logged. But the right answer is a 400
from the route before any signal sees it. I'm marking it held because nothing
crashed and nothing was judged with confidence. It still isn't the ideal
response, and it's listed under **What's Still Broken**.

**Probes after the change:** I didn't re-run them, because the attack set
was the measurement. Offline, `style_signal` returns `None` for the
three-sentence Russian text, so `probe_ru3` would no longer crash.

**My five criteria, after** (`python run_eval.py --label after`, and
`python run_criteria_4_5.py --trial N --label after` for N = 1, 2, 3, with a
restart before each trial):

| Criterion | Target | Before (×3) | After, run 1 | Run 2 | Run 3 | After verdict |
|---|---|---|---|---|---|---|
| 1. My own writing is not called AI | 0 ai **and** ≤ 3 unsure | 0 ai · 7 unsure · 3 human | 0 · 7 · 3 | 0 · 7 · 3 | 0 · 7 · 3 | **MISSED** (unchanged) |
| 2. AI and my writing score far apart | gap ≥ 0.30 | 0.203 | 0.203 | 0.203 | 0.203 | **MISSED** (unchanged) |
| 3. Labels reachable, ordinary AI caught | ≥ 3/5 ai **and** ≥ 2/3 mixed unsure | 3/5 · 2/3 | 3/5 · 2/3 | 3/5 · 2/3 | 3/5 · 2/3 | MET (unchanged) |
| 4. Appeals recorded, invalid ones change nothing | 5/5 · 3/3 · 0 added | 5/5 · 3/3 · 0 | 5/5 · 3/3 · 0 | 5/5 · 3/3 · 0 | 5/5 · 3/3 · 0 | MET (unchanged) |
| 5. Bad input gets a clear 400, never crashes | 9/9 · 0 × 500 · 9/9 logged · not loaded | met on my nine; MF04 crashed | 9/9 · 0 · 9/9 · not loaded | same | same | **MISSED**, see below |

All 23 submissions for criteria 1–3 scored **identically before and after**,
to the fourth decimal place, in every trial. Each one has at least 3
sentences, so the change never touches them. That's evidence that the change
did what I scoped it to do and nothing else. Results:
`results/run_2026-11-13_1809_after.md` and
`results/criteria45_after_trial{1,2,3}_*.json`.

*Criterion 5 after:* the crash is gone. MF04 and three-sentence Russian no
longer return a 500. But the criterion says bad input gets a **clear 400**,
and MF04 now gets a 200 and an unsure label. So I'm keeping it MISSED. The
change moved it from "crashes" to "answers, but with the wrong kind of
answer". That is a real improvement, and it still isn't the target.

**Did it help, and how do I know:**

**Yes, for what it targeted, and it cost something.** Broken attacks went
from 13 to 10. The only crash and the only missing log entry are gone. My
worst outcome, a confident ai label on a sentence of Arabic, is now unsure. I
know the change caused this because exactly the rows with fewer than 3
sentences or no countable words changed, and nothing else did.

**What it cost:** every genuine text under 3 sentences can now **never** be
labelled human. The five flood submissions (FL01) were labelled human before
and are unsure now, and so would be any real writer who submits a short
paragraph. I traded wrong *ai* and *human* labels on short text for no verdict
at all. In unit 7 I decided unsure is the cheaper mistake, because it accuses
no one. But it isn't free. A writer whose every short piece says "we can't
tell" is still being told the check doesn't believe them.

**What it didn't touch, as expected:** criteria 1 and 2 are still missed, with
exactly the same numbers, because they come from groups B and E and from
where the human line sits, not from signal two's edges. Ten attacks still get
through, and none of them was what this change was for.



---

## What's Still Broken

<!-- For each attack still getting through and each criterion still missed:
     what you'd do, and why you stopped. -->



**The trade I'd make if this ran for real:**

<!-- Two sentences. Fewer wrong accusations means more AI text getting through.
     Say which way you'd go and WHO PAYS FOR IT. -->



<!-- ═════════════════════════════════════════════════════════════════════

     SUBMISSION CHECKLIST — unit 7

       [ ] criteria.md has five numbered criteria, each naming a target
       [ ] Each has a reason underneath
       [ ] POST /submit returns content_id, guess, confidence, label,
           model_score and style_score
       [ ] Two signals that measure DIFFERENT things, each with a named blind spot
       [ ] Three label variants, all reachable, written out in full
       [ ] POST /appeal changes status and writes to the log
       [ ] Signals and Scoring names scoring.py::combine_signals
       [ ] Sample Run: a submission AND an appeal, as pasted text
       [ ] At least four new commits
       [ ] Repository URL submitted — WRITE IT DOWN

     SUBMISSION CHECKLIST — unit 8

       [ ] Rate limiting on /submit, with your numbers justified
       [ ] The pasted run of status codes showing 429
       [ ] Audit log with all nine fields, recording rejections too
       [ ] The attack set run IN FULL, every input with an outcome
       [ ] Ten audit log entries pasted as text
       [ ] Five criteria across three trials
       [ ] A diagnosis for every miss and every broken attack — stage AND mechanism
       [ ] One improvement, with Attack Run — After
       [ ] What's Still Broken, including the production trade
       [ ] At least four new commits
       [ ] The SAME repository URL as last unit

     Do not delete and recreate this repository.
     ═════════════════════════════════════════════════════════════════════ -->

---

📖 **How to run this project: [RUNNING.md](RUNNING.md)**
