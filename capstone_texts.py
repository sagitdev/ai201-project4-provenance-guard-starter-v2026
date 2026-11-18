"""
The texts criteria 3 and 4 send, built exactly as criteria.md describes.

    python capstone_texts.py     # prints each text's size, to check against criteria.md

Both capstone_c3.py and capstone_c4.py import from here, so criterion 3's
cold-start text is the same text as criterion 4's first 1,000-word text.
"""

from scenarios import AI_ESSAYS, MIXED, MY_WRITING

# The 18 texts in file order: #1-#10, AI1-AI5, M1-M3.
TEXTS = {**MY_WRITING, **AI_ESSAYS, **MIXED}
ORDER = list(TEXTS)


def key(short):
    """'#7' -> '#7 repo (hard: uniform formal)', 'AI2' -> 'AI2 weekend — ...'"""
    return next(k for k in ORDER if k.split()[0] == short)


def joined(*shorts):
    """Join named texts with one space between them."""
    return " ".join(TEXTS[key(s)] for s in shorts)


def cycle_from(short):
    """Texts in file order, starting at `short`, wrapping after M3 back to #1."""
    i = ORDER.index(key(short))
    while True:
        yield TEXTS[ORDER[i % len(ORDER)]]
        i += 1


def first_words(short, n=1000):
    """Join texts from `short` onward, split on whitespace, keep the first n words."""
    words = []
    texts = cycle_from(short)
    while len(words) < n:
        words += next(texts).split()
    return " ".join(words[:n])


def first_chars(short, limit=49_000):
    """Join whole texts until past `limit` chars, then cut at the last space within it."""
    texts = cycle_from(short)
    s = next(texts)
    while len(s) <= limit:
        s = s + " " + next(texts)
    s = s[:limit]
    return s[:s.rfind(" ")]  # cut at the last space, so we don't split a word


GROUPS = {
    "100w": [TEXTS[key("AI2")], TEXTS[key("AI3")], TEXTS[key("M3")]],
    "300w": [joined("AI5", "#7", "#6"), joined("M1", "#8", "#5"), joined("AI4", "AI1", "M2")],
    "1000w": [first_words("#1"), first_words("AI1"), first_words("M1")],
    "49k": [first_chars("#1"), first_chars("AI1"), first_chars("M1")],
}

# Criterion 3: the first text of criterion 4's 1,000-word group.
COLD_START_TEXT = GROUPS["1000w"][0]


if __name__ == "__main__":
    from transformers import AutoTokenizer

    tok = AutoTokenizer.from_pretrained("gpt2")
    for group, texts in GROUPS.items():
        for i, t in enumerate(texts, start=1):
            print(f"{group:6} text {i}: {len(t.split()):6} words  "
                  f"{len(t):6} chars  {len(tok(t)['input_ids']):6} tokens")