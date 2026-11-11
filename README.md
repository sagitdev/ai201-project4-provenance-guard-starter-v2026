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



---

## Signals and Scoring

<!-- For each signal: what property it measures, why that might differ between
     human and AI writing, and WHAT IT CAN'T SEE.

     The blind spot is not optional. If you can't name it you don't understand
     the signal yet — and unit 8's attack set is built out of blind spots. -->

### Signal one — the model signal

**What it measures:**

**Why that might differ between human and AI writing:**

**What it can't see:**

### Signal two — the style signal

**What it measures:**

**Why that might differ between human and AI writing:**

**What it can't see:**

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
| high-confidence human |  |  |
| unsure |  |  |
| high-confidence AI |  |  |

**Why I worded the "unsure" one this way:**
<!-- It's the hardest of the three. It has to admit uncertainty without
     sounding like an accusation, because the person reading it may well have
     written every word themselves. -->



---

## Sample Run

<!-- One submission and one appeal, pasted as text: the request, the response,
     and the log entries. -->

**A submission**

<!-- The response needs content_id, guess, confidence, label, AND both
     signal scores - model_score and style_score. Unit 8's tools read those
     two off the response, so leaving them out costs you next unit's
     diagnostics. -->

```bash
$ curl -X POST http://127.0.0.1:5000/submit \
  -H "Content-Type: application/json" \
  -d '{"text": "My hometown is Changzhi, a city in Shanxi Province. It has four distinct seasons and a lot of green space.", "creator_id": "tank"}'
```

<!-- Milestone 3 run: signal one only. style_score and label are placeholders
     until milestones 4 and 5; this gets replaced with the final run. -->

```json
{
  "confidence": 0.6769,
  "content_id": "d1aa33c3-b470-42e1-abd8-2418b663dc56",
  "guess": "unsure",
  "label": "PLACEHOLDER",
  "model_score": 0.6769,
  "style_score": null
}
```

**An appeal**

```bash
$ curl -X POST http://127.0.0.1:5000/appeal \
  -H "Content-Type: application/json" \
  -d '{"content_id": "...", "reasoning": "..."}'
```

```json

```

**What the log shows afterwards**

```bash
$ curl "http://127.0.0.1:5000/log?limit=3"
```

```json
{
  "count": 2,
  "entries": [
    {
      "creator_id": "tank",
      "event": "rejected",
      "reason": "text_missing",
      "status": "rejected",
      "timestamp": "2026-11-10T04:55:24+00:00"
    },
    {
      "combined_score": 0.6769,
      "content_id": "d1aa33c3-b470-42e1-abd8-2418b663dc56",
      "creator_id": "tank",
      "guess": "unsure",
      "label": "PLACEHOLDER",
      "model_score": 0.6769,
      "status": "decided",
      "style_score": null,
      "timestamp": "2026-11-10T19:41:54+00:00"
    }
  ]
}
```

---

## How I Used AI

**Moment 1**

- *What I asked for:*
- *What came back:*
- *What I changed:*

**Moment 2**

- *What I asked for:*
- *What came back:*
- *What I changed:*

<!-- ═══════════════════════ UNIT 8 — THE TEST ═══════════════════════ -->

---

## Rate Limiting

**My limits:** ___ per minute, ___ per day

**Why those numbers and not others:**
<!-- Think about two people: a real writer submitting their own work a few
     times an hour, and a script sending a thousand variations to map your
     thresholds. Your numbers have to be liveable for the first and hostile to
     the second. -->

**What a caller counts as:** <!-- per address, or per creator_id? They fail
differently — one script can look like a thousand callers, and one household
can look like one. -->

**The run of status codes when I pushed past it:**

<!-- python run_attacks.py --flood 15 -->

```

```

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
