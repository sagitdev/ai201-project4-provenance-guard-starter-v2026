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

<!-- Every attack with its outcome and a held-or-broke mark.
     `run_attacks.py --label before` produces the table. -->



**Ten audit log entries from the run**

<!-- Choose entries that show the interesting failures, not the ten easiest. -->

```json

```

**The single worst outcome** — the one I'd least want to explain to a writer
whose work got caught by it:



---

## Run Log and Verdicts

<!-- Your five criteria across three trials. `run_eval.py --label before`. -->

| Criterion | Target | Run 1 | Run 2 | Run 3 | Verdict |
|---|---|---|---|---|---|
| 1.  |  |  |  |  |  |
| 2.  |  |  |  |  |  |
| 3.  |  |  |  |  |  |
| 4.  |  |  |  |  |  |
| 5.  |  |  |  |  |  |

**Real output from one trial**, pasted as text, naming the file and function
that produced it:

```json

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



---

## The Improvement

**What I changed:**

**Which diagnosis pointed at it:**

### Attack Run — After

<!-- Same format. `run_attacks.py --label after` -->



**Did it help, and how do I know:**

<!-- Widening the unsure band usually fixes one problem and creates another.
     Reporting that trade honestly is worth full credit. -->



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
