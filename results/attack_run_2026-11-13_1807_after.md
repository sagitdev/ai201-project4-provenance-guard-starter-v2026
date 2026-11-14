# Attack run — after

- Produced by: `run_attacks.py::main`
- Service: `app.py::submit`
- 56 attacks · 2026-11-13 18:07
- Auto-marked BROKE (5xx, crash, no response): **0**
- Left for you to judge: **56**

The Verdict column is blank where a script can't honestly decide. Whether
an evasion worked depends on where you put your thresholds — read the
`targets` column, look at what came back, and write HELD or BROKE yourself.

Each attack submits as creator_id `attacker_<id>`, and the content_id it
came back with is in the table — either one will match this run against your
audit log when you go looking for the ten entries to paste.

| ID | Family | Targeting | Status | Content ID | Guess | Score | Verdict |
|---|---|---|---|---|---|---|---|
| EV01 | evasion | signal two: typos raise word variety | 200 | `77dafdb8-3bd2-418d-8f16-bf3834007ea0` | human | 0.378 |  |
| EV02 | evasion | signal two: broken-up sentences raise length spread | 200 | `88a54b1b-cb71-42a2-88ff-61b6641bdfb3` | human | 0.416 |  |
| EV03 | evasion | signal two: a pasted quotation changes the shape | 200 | `d556fe9e-520c-4b8b-954e-57796723c198` | unsure | 0.560 |  |
| EV04 | evasion | signal one: unusual words raise perplexity | 200 | `8389bed7-259b-48bc-9201-47733a64f043` | ai | 0.683 |  |
| EV05 | evasion | both signals: heavy human editing pass | 200 | `3d42d255-c1ad-4d2d-8c4e-95a3572834ca` | human | 0.225 |  |
| EV06 | evasion | signal two: one very long sentence and one very short | 200 | `ee4da637-8c92-481f-ad0f-1dd0daf15ca5` | human | 0.401 |  |
| EV07 | evasion | signal two: padding with punctuation | 200 | `36ca3d96-929e-4a82-a145-790ca7d25462` | unsure | 0.586 |  |
| EV08 | evasion | signal one: text below the token window | 200 | `c33bb024-0edb-405e-bb85-bfa2f05bf3ad` | unsure | 0.510 |  |
| EV09 | evasion | both: AI text with a human opening paragraph bolted on | 200 | `aab575b0-2977-48d5-9514-92b58030715c` | unsure | 0.572 |  |
| EV10 | evasion | signal two: repeated stanza structure | 200 | `1c6e50d6-f71a-4456-a970-121681c894d0` | unsure | 0.640 |  |
| FP01 | false_positive | plain, clear human writing with no flourishes | 200 | `ac43a89c-97a1-48ec-b104-ba2ad1d804d4` | unsure | 0.518 |  |
| FP02 | false_positive | human writing in a formal register | 200 | `82ed1731-9f6a-4d67-adf1-cfc32c62efd8` | ai | 0.733 |  |
| FP03 | false_positive | a non-native English speaker writing carefully | 200 | `68739f5c-4680-4b9c-87f4-cc2394d5d340` | ai | 0.727 |  |
| FP04 | false_positive | a student essay written to a rubric | 200 | `d2504779-d91e-4784-a736-437c5586012c` | ai | 0.723 |  |
| FP05 | false_positive | technical documentation written by a person | 200 | `eaf71469-248d-4cf8-b668-2f647d7bf58b` | ai | 0.754 |  |
| FP06 | false_positive | a person imitating a formal template | 200 | `06d728d7-b1a4-44f4-8781-3d732d30d174` | unsure | 0.640 |  |
| FP07 | false_positive | human writing that repeats a phrase deliberately | 200 | `a8618b72-1092-467f-ab04-3e426fd7cf8a` | unsure | 0.617 |  |
| FP08 | false_positive | very short genuine human submission | 200 | `e9cf911a-01a2-4b56-b778-03dc6ff4e16f` | human | 0.326 |  |
| PI01 | prompt_injection | instruction to ignore the check | 200 | `0dac9485-edc3-4bc3-8f5a-9f1567010292` | human | 0.324 |  |
| PI02 | prompt_injection | instruction disguised as a system message | 200 | `9b9cb93f-16a7-4532-a589-b38cd3f63ac3` | human | 0.143 |  |
| PI03 | prompt_injection | instruction wrapped in the writer's voice | 200 | `83680cd8-63db-4e30-ac55-df5e66973301` | unsure | 0.570 |  |
| PI04 | prompt_injection | attempt to make the label text hostile | 200 | `2f2526d1-1159-4812-88b4-cb8f9ea9cc81` | human | 0.472 |  |
| PI05 | prompt_injection | attempt to inject into the audit log | 200 | `fe8ca576-e984-4b27-81bd-2182665679d2` | unsure | 0.640 |  |
| PI06 | prompt_injection | instruction plus real human text | 200 | `933221b2-d913-4ad1-b27f-95a1fa1bf339` | human | 0.483 |  |
| MF01 | malformed | text is only whitespace | 400 | `—` | — | — |  |
| MF02 | malformed | text is a single character | 400 | `—` | — | — |  |
| MF03 | malformed | text is control characters | 400 | `—` | — | — |  |
| MF04 | malformed | text is only punctuation | 200 | `58b1882b-aca8-4dec-a938-c070c27603e0` | unsure | 0.510 |  |
| MF05 | malformed | text is a very long single word | 400 | `—` | — | — |  |
| MF06 | malformed | text is emoji only | 400 | `—` | — | — |  |
| MF07 | malformed | text is right-to-left script | 200 | `22ee265f-9437-45a2-a231-f89d6100d354` | unsure | 0.640 |  |
| MF08 | malformed | text is 60,000 characters | 400 | `—` | — | — |  |
| RQ01 | malformed | no text field at all | 400 | `—` | — | — |  |
| RQ02 | malformed | no creator_id | 400 | `—` | — | — |  |
| RQ03 | malformed | text is a number | 400 | `—` | — | — |  |
| RQ04 | malformed | text is a list | 400 | `—` | — | — |  |
| RQ05 | malformed | text is null | 400 | `—` | — | — |  |
| RQ06 | malformed | creator_id is an object | 400 | `—` | — | — |  |
| RQ07 | malformed | body is a JSON array, not an object | 400 | `—` | — | — |  |
| RQ08 | malformed | body is unparseable JSON | 400 | `—` | — | — |  |
| RQ09 | malformed | body is empty | 400 | `—` | — | — |  |
| RQ10 | malformed | body is form-encoded, not JSON | 429 | `—` | — | — |  |
| RQ11 | malformed | body is JSON claiming to be plain text | 429 | `—` | — | — |  |
| RQ12 | malformed | deeply nested JSON | 400 | `—` | — | — |  |
| FL01_01 | flood_same_creator | 20 rapid submissions from one creator | 200 | `17556f2b-7801-4028-aa0f-4f800ee8ed60` | unsure | 0.510 |  |
| FL01_02 | flood_same_creator | 20 rapid submissions from one creator | 200 | `d6f3b522-d882-4f05-9f81-4e4acba3b661` | unsure | 0.510 |  |
| FL01_03 | flood_same_creator | 20 rapid submissions from one creator | 200 | `913beeb6-95d9-4e0a-8ed1-60dde45d6600` | unsure | 0.510 |  |
| FL01_04 | flood_same_creator | 20 rapid submissions from one creator | 200 | `15f24db7-e129-4bc3-a7e1-a53f4c037e00` | unsure | 0.510 |  |
| FL01_05 | flood_same_creator | 20 rapid submissions from one creator | 200 | `22971785-3e61-49d0-90bb-23a7ba68a7e5` | unsure | 0.510 |  |
| FL01_06 | flood_same_creator | 20 rapid submissions from one creator | 429 | `—` | — | — |  |
| FL01_07 | flood_same_creator | 20 rapid submissions from one creator | 429 | `—` | — | — |  |
| FL01_08 | flood_same_creator | 20 rapid submissions from one creator | 429 | `—` | — | — |  |
| FL01_09 | flood_same_creator | 20 rapid submissions from one creator | 429 | `—` | — | — |  |
| FL01_10 | flood_same_creator | 20 rapid submissions from one creator | 429 | `—` | — | — |  |
| FL01_11 | flood_same_creator | 20 rapid submissions from one creator | 429 | `—` | — | — |  |
| FL01_12 | flood_same_creator | 20 rapid submissions from one creator | 429 | `—` | — | — |  |

---

## By family

| Family | Attacks | Auto-BROKE | Left to judge |
|---|---|---|---|
| `evasion` | 10 | 0 | 10 |
| `false_positive` | 8 | 0 | 8 |
| `flood_same_creator` | 12 | 0 | 12 |
| `malformed` | 20 | 0 | 20 |
| `prompt_injection` | 6 | 0 | 6 |

> The **false_positive** family is the one to look at hardest. Those are
> written to be genuine human writing that reads as machine-like. Every one
> your service calls AI is a real writer it would have accused.

---

## What came back

The detail behind the table. Paste the interesting failures into your
README — the ones that show something, not the ten easiest.

### EV01 — `evasion`

*Targeting:* signal two: typos raise word variety

```json
{
  "id": "EV01",
  "status": 200,
  "content_id": "77dafdb8-3bd2-418d-8f16-bf3834007ea0",
  "creator_id": "attacker_EV01",
  "guess": "human",
  "confidence": 0.378,
  "model_score": 0.1635,
  "style_score": 0.8785,
  "label": "We think this was most likely written by a person.",
  "error": null,
  "verdict": ""
}
```

### EV02 — `evasion`

*Targeting:* signal two: broken-up sentences raise length spread

```json
{
  "id": "EV02",
  "status": 200,
  "content_id": "88a54b1b-cb71-42a2-88ff-61b6641bdfb3",
  "creator_id": "attacker_EV02",
  "guess": "human",
  "confidence": 0.416,
  "model_score": 0.5943,
  "style_score": 0.0,
  "label": "We think this was most likely written by a person.",
  "error": null,
  "verdict": ""
}
```

### EV03 — `evasion`

*Targeting:* signal two: a pasted quotation changes the shape

```json
{
  "id": "EV03",
  "status": 200,
  "content_id": "d556fe9e-520c-4b8b-954e-57796723c198",
  "creator_id": "attacker_EV03",
  "guess": "unsure",
  "confidence": 0.5603,
  "model_score": 0.6662,
  "style_score": 0.3132,
  "label": "We can't tell how this was written \u2014 our check has its limits. Nothing happens because of this result. If you'd like a person to take a look, you can request a review. A review can make the result more objective.",
  "error": null,
  "verdict": ""
}
```

### EV04 — `evasion`

*Targeting:* signal one: unusual words raise perplexity

```json
{
  "id": "EV04",
  "status": 200,
  "content_id": "8389bed7-259b-48bc-9201-47733a64f043",
  "creator_id": "attacker_EV04",
  "guess": "ai",
  "confidence": 0.6835,
  "model_score": 0.6114,
  "style_score": 0.8519,
  "label": "We think this was most likely written by AI. Nothing happens because of this result. If you think this result is wrong, you can request a review. A person can see things our check can't.",
  "error": null,
  "verdict": ""
}
```

### EV05 — `evasion`

*Targeting:* both signals: heavy human editing pass

```json
{
  "id": "EV05",
  "status": 200,
  "content_id": "3d42d255-c1ad-4d2d-8c4e-95a3572834ca",
  "creator_id": "attacker_EV05",
  "guess": "human",
  "confidence": 0.2248,
  "model_score": 0.3212,
  "style_score": 0.0,
  "label": "We think this was most likely written by a person.",
  "error": null,
  "verdict": ""
}
```

### EV06 — `evasion`

*Targeting:* signal two: one very long sentence and one very short

```json
{
  "id": "EV06",
  "status": 200,
  "content_id": "ee4da637-8c92-481f-ad0f-1dd0daf15ca5",
  "creator_id": "attacker_EV06",
  "guess": "human",
  "confidence": 0.4009,
  "model_score": 0.5727,
  "style_score": 0.0,
  "label": "We think this was most likely written by a person.",
  "error": null,
  "verdict": ""
}
```

### EV07 — `evasion`

*Targeting:* signal two: padding with punctuation

```json
{
  "id": "EV07",
  "status": 200,
  "content_id": "36ca3d96-929e-4a82-a145-790ca7d25462",
  "creator_id": "attacker_EV07",
  "guess": "unsure",
  "confidence": 0.5862,
  "model_score": 0.5862,
  "style_score": null,
  "label": "We can't tell how this was written \u2014 our check has its limits. Nothing happens because of this result. If you'd like a person to take a look, you can request a review. A review can make the result more objective.",
  "error": null,
  "verdict": ""
}
```

### EV08 — `evasion`

*Targeting:* signal one: text below the token window

```json
{
  "id": "EV08",
  "status": 200,
  "content_id": "c33bb024-0edb-405e-bb85-bfa2f05bf3ad",
  "creator_id": "attacker_EV08",
  "guess": "unsure",
  "confidence": 0.51,
  "model_score": 0.2452,
  "style_score": null,
  "label": "We can't tell how this was written \u2014 our check has its limits. Nothing happens because of this result. If you'd like a person to take a look, you can request a review. A review can make the result more objective.",
  "error": null,
  "verdict": ""
}
```

### EV09 — `evasion`

*Targeting:* both: AI text with a human opening paragraph bolted on

```json
{
  "id": "EV09",
  "status": 200,
  "content_id": "aab575b0-2977-48d5-9514-92b58030715c",
  "creator_id": "attacker_EV09",
  "guess": "unsure",
  "confidence": 0.5724,
  "model_score": 0.7042,
  "style_score": 0.2649,
  "label": "We can't tell how this was written \u2014 our check has its limits. Nothing happens because of this result. If you'd like a person to take a look, you can request a review. A review can make the result more objective.",
  "error": null,
  "verdict": ""
}
```

### EV10 — `evasion`

*Targeting:* signal two: repeated stanza structure

```json
{
  "id": "EV10",
  "status": 200,
  "content_id": "1c6e50d6-f71a-4456-a970-121681c894d0",
  "creator_id": "attacker_EV10",
  "guess": "unsure",
  "confidence": 0.64,
  "model_score": 0.9792,
  "style_score": 0.4122,
  "label": "We can't tell how this was written \u2014 our check has its limits. Nothing happens because of this result. If you'd like a person to take a look, you can request a review. A review can make the result more objective.",
  "error": null,
  "verdict": ""
}
```

### FP01 — `false_positive`

*Targeting:* plain, clear human writing with no flourishes

```json
{
  "id": "FP01",
  "status": 200,
  "content_id": "ac43a89c-97a1-48ec-b104-ba2ad1d804d4",
  "creator_id": "attacker_FP01",
  "guess": "unsure",
  "confidence": 0.5178,
  "model_score": 0.6175,
  "style_score": 0.285,
  "label": "We can't tell how this was written \u2014 our check has its limits. Nothing happens because of this result. If you'd like a person to take a look, you can request a review. A review can make the result more objective.",
  "error": null,
  "verdict": ""
}
```

### FP02 — `false_positive`

*Targeting:* human writing in a formal register

```json
{
  "id": "FP02",
  "status": 200,
  "content_id": "82ed1731-9f6a-4d67-adf1-cfc32c62efd8",
  "creator_id": "attacker_FP02",
  "guess": "ai",
  "confidence": 0.7329,
  "model_score": 0.7387,
  "style_score": 0.7193,
  "label": "We think this was most likely written by AI. Nothing happens because of this result. If you think this result is wrong, you can request a review. A person can see things our check can't.",
  "error": null,
  "verdict": ""
}
```

### FP03 — `false_positive`

*Targeting:* a non-native English speaker writing carefully

```json
{
  "id": "FP03",
  "status": 200,
  "content_id": "68739f5c-4680-4b9c-87f4-cc2394d5d340",
  "creator_id": "attacker_FP03",
  "guess": "ai",
  "confidence": 0.7267,
  "model_score": 0.8051,
  "style_score": 0.5436,
  "label": "We think this was most likely written by AI. Nothing happens because of this result. If you think this result is wrong, you can request a review. A person can see things our check can't.",
  "error": null,
  "verdict": ""
}
```

### FP04 — `false_positive`

*Targeting:* a student essay written to a rubric

```json
{
  "id": "FP04",
  "status": 200,
  "content_id": "d2504779-d91e-4784-a736-437c5586012c",
  "creator_id": "attacker_FP04",
  "guess": "ai",
  "confidence": 0.723,
  "model_score": 0.8329,
  "style_score": 0.4666,
  "label": "We think this was most likely written by AI. Nothing happens because of this result. If you think this result is wrong, you can request a review. A person can see things our check can't.",
  "error": null,
  "verdict": ""
}
```

### FP05 — `false_positive`

*Targeting:* technical documentation written by a person

```json
{
  "id": "FP05",
  "status": 200,
  "content_id": "eaf71469-248d-4cf8-b668-2f647d7bf58b",
  "creator_id": "attacker_FP05",
  "guess": "ai",
  "confidence": 0.7542,
  "model_score": 0.8005,
  "style_score": 0.6462,
  "label": "We think this was most likely written by AI. Nothing happens because of this result. If you think this result is wrong, you can request a review. A person can see things our check can't.",
  "error": null,
  "verdict": ""
}
```

### FP06 — `false_positive`

*Targeting:* a person imitating a formal template

```json
{
  "id": "FP06",
  "status": 200,
  "content_id": "06d728d7-b1a4-44f4-8781-3d732d30d174",
  "creator_id": "attacker_FP06",
  "guess": "unsure",
  "confidence": 0.64,
  "model_score": 0.8814,
  "style_score": 0.1617,
  "label": "We can't tell how this was written \u2014 our check has its limits. Nothing happens because of this result. If you'd like a person to take a look, you can request a review. A review can make the result more objective.",
  "error": null,
  "verdict": ""
}
```

### FP07 — `false_positive`

*Targeting:* human writing that repeats a phrase deliberately

```json
{
  "id": "FP07",
  "status": 200,
  "content_id": "a8618b72-1092-467f-ab04-3e426fd7cf8a",
  "creator_id": "attacker_FP07",
  "guess": "unsure",
  "confidence": 0.6171,
  "model_score": 0.8816,
  "style_score": 0.0,
  "label": "We can't tell how this was written \u2014 our check has its limits. Nothing happens because of this result. If you'd like a person to take a look, you can request a review. A review can make the result more objective.",
  "error": null,
  "verdict": ""
}
```

### FP08 — `false_positive`

*Targeting:* very short genuine human submission

```json
{
  "id": "FP08",
  "status": 200,
  "content_id": "e9cf911a-01a2-4b56-b778-03dc6ff4e16f",
  "creator_id": "attacker_FP08",
  "guess": "human",
  "confidence": 0.3258,
  "model_score": 0.3223,
  "style_score": 0.334,
  "label": "We think this was most likely written by a person.",
  "error": null,
  "verdict": ""
}
```

### PI01 — `prompt_injection`

*Targeting:* instruction to ignore the check

```json
{
  "id": "PI01",
  "status": 200,
  "content_id": "0dac9485-edc3-4bc3-8f5a-9f1567010292",
  "creator_id": "attacker_PI01",
  "guess": "human",
  "confidence": 0.3237,
  "model_score": 0.4625,
  "style_score": 0.0,
  "label": "We think this was most likely written by a person.",
  "error": null,
  "verdict": ""
}
```

### PI02 — `prompt_injection`

*Targeting:* instruction disguised as a system message

```json
{
  "id": "PI02",
  "status": 200,
  "content_id": "9b9cb93f-16a7-4532-a589-b38cd3f63ac3",
  "creator_id": "attacker_PI02",
  "guess": "human",
  "confidence": 0.1431,
  "model_score": 0.2044,
  "style_score": 0.0,
  "label": "We think this was most likely written by a person.",
  "error": null,
  "verdict": ""
}
```

### PI03 — `prompt_injection`

*Targeting:* instruction wrapped in the writer's voice

```json
{
  "id": "PI03",
  "status": 200,
  "content_id": "83680cd8-63db-4e30-ac55-df5e66973301",
  "creator_id": "attacker_PI03",
  "guess": "unsure",
  "confidence": 0.5702,
  "model_score": 0.5943,
  "style_score": 0.5139,
  "label": "We can't tell how this was written \u2014 our check has its limits. Nothing happens because of this result. If you'd like a person to take a look, you can request a review. A review can make the result more objective.",
  "error": null,
  "verdict": ""
}
```

### PI04 — `prompt_injection`

*Targeting:* attempt to make the label text hostile

```json
{
  "id": "PI04",
  "status": 200,
  "content_id": "2f2526d1-1159-4812-88b4-cb8f9ea9cc81",
  "creator_id": "attacker_PI04",
  "guess": "human",
  "confidence": 0.4718,
  "model_score": 0.4998,
  "style_score": 0.4066,
  "label": "We think this was most likely written by a person.",
  "error": null,
  "verdict": ""
}
```

### PI05 — `prompt_injection`

*Targeting:* attempt to inject into the audit log

```json
{
  "id": "PI05",
  "status": 200,
  "content_id": "fe8ca576-e984-4b27-81bd-2182665679d2",
  "creator_id": "attacker_PI05",
  "guess": "unsure",
  "confidence": 0.64,
  "model_score": 0.6401,
  "style_score": null,
  "label": "We can't tell how this was written \u2014 our check has its limits. Nothing happens because of this result. If you'd like a person to take a look, you can request a review. A review can make the result more objective.",
  "error": null,
  "verdict": ""
}
```

### PI06 — `prompt_injection`

*Targeting:* instruction plus real human text

```json
{
  "id": "PI06",
  "status": 200,
  "content_id": "933221b2-d913-4ad1-b27f-95a1fa1bf339",
  "creator_id": "attacker_PI06",
  "guess": "human",
  "confidence": 0.4835,
  "model_score": 0.5583,
  "style_score": 0.3091,
  "label": "We think this was most likely written by a person.",
  "error": null,
  "verdict": ""
}
```

### MF01 — `malformed`

*Targeting:* text is only whitespace

```json
{
  "id": "MF01",
  "status": 400,
  "content_id": null,
  "creator_id": "attacker_MF01",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### MF02 — `malformed`

*Targeting:* text is a single character

```json
{
  "id": "MF02",
  "status": 400,
  "content_id": null,
  "creator_id": "attacker_MF02",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### MF03 — `malformed`

*Targeting:* text is control characters

```json
{
  "id": "MF03",
  "status": 400,
  "content_id": null,
  "creator_id": "attacker_MF03",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### MF04 — `malformed`

*Targeting:* text is only punctuation

```json
{
  "id": "MF04",
  "status": 200,
  "content_id": "58b1882b-aca8-4dec-a938-c070c27603e0",
  "creator_id": "attacker_MF04",
  "guess": "unsure",
  "confidence": 0.51,
  "model_score": 0.0112,
  "style_score": null,
  "label": "We can't tell how this was written \u2014 our check has its limits. Nothing happens because of this result. If you'd like a person to take a look, you can request a review. A review can make the result more objective.",
  "error": null,
  "verdict": ""
}
```

### MF05 — `malformed`

*Targeting:* text is a very long single word

```json
{
  "id": "MF05",
  "status": 400,
  "content_id": null,
  "creator_id": "attacker_MF05",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### MF06 — `malformed`

*Targeting:* text is emoji only

```json
{
  "id": "MF06",
  "status": 400,
  "content_id": null,
  "creator_id": "attacker_MF06",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### MF07 — `malformed`

*Targeting:* text is right-to-left script

```json
{
  "id": "MF07",
  "status": 200,
  "content_id": "22ee265f-9437-45a2-a231-f89d6100d354",
  "creator_id": "attacker_MF07",
  "guess": "unsure",
  "confidence": 0.64,
  "model_score": 0.9064,
  "style_score": null,
  "label": "We can't tell how this was written \u2014 our check has its limits. Nothing happens because of this result. If you'd like a person to take a look, you can request a review. A review can make the result more objective.",
  "error": null,
  "verdict": ""
}
```

### MF08 — `malformed`

*Targeting:* text is 60,000 characters

```json
{
  "id": "MF08",
  "status": 400,
  "content_id": null,
  "creator_id": "attacker_MF08",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### RQ01 — `malformed`

*Targeting:* no text field at all

```json
{
  "id": "RQ01",
  "status": 400,
  "content_id": null,
  "creator_id": "attacker_RQ01",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### RQ02 — `malformed`

*Targeting:* no creator_id

```json
{
  "id": "RQ02",
  "status": 400,
  "content_id": null,
  "creator_id": null,
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### RQ03 — `malformed`

*Targeting:* text is a number

```json
{
  "id": "RQ03",
  "status": 400,
  "content_id": null,
  "creator_id": "attacker_RQ03",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### RQ04 — `malformed`

*Targeting:* text is a list

```json
{
  "id": "RQ04",
  "status": 400,
  "content_id": null,
  "creator_id": "attacker_RQ04",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### RQ05 — `malformed`

*Targeting:* text is null

```json
{
  "id": "RQ05",
  "status": 400,
  "content_id": null,
  "creator_id": "attacker_RQ05",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### RQ06 — `malformed`

*Targeting:* creator_id is an object

```json
{
  "id": "RQ06",
  "status": 400,
  "content_id": null,
  "creator_id": {
    "id": "x"
  },
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### RQ07 — `malformed`

*Targeting:* body is a JSON array, not an object

```json
{
  "id": "RQ07",
  "status": 400,
  "content_id": null,
  "creator_id": null,
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### RQ08 — `malformed`

*Targeting:* body is unparseable JSON

```json
{
  "id": "RQ08",
  "status": 400,
  "content_id": null,
  "creator_id": null,
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### RQ09 — `malformed`

*Targeting:* body is empty

```json
{
  "id": "RQ09",
  "status": 400,
  "content_id": null,
  "creator_id": null,
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### RQ10 — `malformed`

*Targeting:* body is form-encoded, not JSON

```json
{
  "id": "RQ10",
  "status": 429,
  "content_id": null,
  "creator_id": null,
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### RQ11 — `malformed`

*Targeting:* body is JSON claiming to be plain text

```json
{
  "id": "RQ11",
  "status": 429,
  "content_id": null,
  "creator_id": null,
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### RQ12 — `malformed`

*Targeting:* deeply nested JSON

```json
{
  "id": "RQ12",
  "status": 400,
  "content_id": null,
  "creator_id": "attacker_RQ12",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### FL01_01 — `flood_same_creator`

*Targeting:* 20 rapid submissions from one creator

```json
{
  "id": "FL01_01",
  "status": 200,
  "content_id": "17556f2b-7801-4028-aa0f-4f800ee8ed60",
  "creator_id": "attacker_flood",
  "guess": "unsure",
  "confidence": 0.51,
  "model_score": 0.0287,
  "style_score": null,
  "label": "We can't tell how this was written \u2014 our check has its limits. Nothing happens because of this result. If you'd like a person to take a look, you can request a review. A review can make the result more objective.",
  "error": null,
  "verdict": ""
}
```

### FL01_02 — `flood_same_creator`

*Targeting:* 20 rapid submissions from one creator

```json
{
  "id": "FL01_02",
  "status": 200,
  "content_id": "d6f3b522-d882-4f05-9f81-4e4acba3b661",
  "creator_id": "attacker_flood",
  "guess": "unsure",
  "confidence": 0.51,
  "model_score": 0.0287,
  "style_score": null,
  "label": "We can't tell how this was written \u2014 our check has its limits. Nothing happens because of this result. If you'd like a person to take a look, you can request a review. A review can make the result more objective.",
  "error": null,
  "verdict": ""
}
```

### FL01_03 — `flood_same_creator`

*Targeting:* 20 rapid submissions from one creator

```json
{
  "id": "FL01_03",
  "status": 200,
  "content_id": "913beeb6-95d9-4e0a-8ed1-60dde45d6600",
  "creator_id": "attacker_flood",
  "guess": "unsure",
  "confidence": 0.51,
  "model_score": 0.0287,
  "style_score": null,
  "label": "We can't tell how this was written \u2014 our check has its limits. Nothing happens because of this result. If you'd like a person to take a look, you can request a review. A review can make the result more objective.",
  "error": null,
  "verdict": ""
}
```

### FL01_04 — `flood_same_creator`

*Targeting:* 20 rapid submissions from one creator

```json
{
  "id": "FL01_04",
  "status": 200,
  "content_id": "15f24db7-e129-4bc3-a7e1-a53f4c037e00",
  "creator_id": "attacker_flood",
  "guess": "unsure",
  "confidence": 0.51,
  "model_score": 0.0287,
  "style_score": null,
  "label": "We can't tell how this was written \u2014 our check has its limits. Nothing happens because of this result. If you'd like a person to take a look, you can request a review. A review can make the result more objective.",
  "error": null,
  "verdict": ""
}
```

### FL01_05 — `flood_same_creator`

*Targeting:* 20 rapid submissions from one creator

```json
{
  "id": "FL01_05",
  "status": 200,
  "content_id": "22971785-3e61-49d0-90bb-23a7ba68a7e5",
  "creator_id": "attacker_flood",
  "guess": "unsure",
  "confidence": 0.51,
  "model_score": 0.0287,
  "style_score": null,
  "label": "We can't tell how this was written \u2014 our check has its limits. Nothing happens because of this result. If you'd like a person to take a look, you can request a review. A review can make the result more objective.",
  "error": null,
  "verdict": ""
}
```

### FL01_06 — `flood_same_creator`

*Targeting:* 20 rapid submissions from one creator

```json
{
  "id": "FL01_06",
  "status": 429,
  "content_id": null,
  "creator_id": "attacker_flood",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### FL01_07 — `flood_same_creator`

*Targeting:* 20 rapid submissions from one creator

```json
{
  "id": "FL01_07",
  "status": 429,
  "content_id": null,
  "creator_id": "attacker_flood",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### FL01_08 — `flood_same_creator`

*Targeting:* 20 rapid submissions from one creator

```json
{
  "id": "FL01_08",
  "status": 429,
  "content_id": null,
  "creator_id": "attacker_flood",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### FL01_09 — `flood_same_creator`

*Targeting:* 20 rapid submissions from one creator

```json
{
  "id": "FL01_09",
  "status": 429,
  "content_id": null,
  "creator_id": "attacker_flood",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### FL01_10 — `flood_same_creator`

*Targeting:* 20 rapid submissions from one creator

```json
{
  "id": "FL01_10",
  "status": 429,
  "content_id": null,
  "creator_id": "attacker_flood",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### FL01_11 — `flood_same_creator`

*Targeting:* 20 rapid submissions from one creator

```json
{
  "id": "FL01_11",
  "status": 429,
  "content_id": null,
  "creator_id": "attacker_flood",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### FL01_12 — `flood_same_creator`

*Targeting:* 20 rapid submissions from one creator

```json
{
  "id": "FL01_12",
  "status": 429,
  "content_id": null,
  "creator_id": "attacker_flood",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```
