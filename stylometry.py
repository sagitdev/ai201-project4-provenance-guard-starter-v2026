"""
Signal two: the style signal. ← YOU BUILD THIS IN MILESTONE 4

Signal one reads the text for meaning. This one measures it *as text* — the
shape of it, without understanding a word.

Three measures are stubbed below because the brief names those three. They are
stubs, not implementations: what they compute is yours, and so is how you
combine them.

    sentence_length_spread   do sentences vary in length, or march in step?
    type_token_ratio         how much of the vocabulary repeats?
    punctuation_density      how much punctuation, and how varied?

Why these might differ between human and AI writing: generated prose tends
toward even, mid-length sentences and a narrower band of vocabulary, because
that's what "most likely next word" produces on average. Human writing is
lumpier — a three-word sentence next to a forty-word one.

⚠️ **The blind spot, which you have to name in Milestone 1.**

This signal cannot read. It has no idea what the text says. Anything that
changes the shape without changing the substance moves it — adding typos,
breaking up sentences, pasting in a quotation. That is a very cheap thing for
someone to do on purpose, and unit 8's attack set will do it to you.

Build each function on its own and call it from a terminal before you wire
anything together:

    python stylometry.py "some text to look at"
"""

import re
import statistics

# 把文本切成句子的列表（按 . ! ? 切）
def sentences(text: str) -> list[str]:
    """Split into sentences. Rough and good enough — given to you."""
    parts = re.split(r"(?<=[.!?])\s+", text.strip())
    return [p for p in parts if p.strip()]

# 把文本切成小写单词的列表，去掉标点
def words(text: str) -> list[str]:
    """Split into lowercase words, punctuation stripped. Given to you."""
    return re.findall(r"[a-z0-9']+", text.lower())


# ── The three measures — YOU BUILD THESE ─────────────────────────────────────

# 指标1：句长离散度
def sentence_length_spread(text: str) -> float:
    """
    How much sentence length varies. ← TODO

    Returns:
        A float. Decide yourself what scale it's on and which direction means
        "more human" — then write that down, because your combining rule
        depends on knowing it.

    A hint on what you're reaching for: the standard deviation of sentence
    lengths, probably divided by the mean so a long text and a short one are
    comparable. `statistics.stdev` is imported for you.

    Watch the edge case: a one-sentence submission has no spread at all, and
    `stdev` raises on fewer than two values. Decide what that should return
    before the attack set decides for you.
    """
    # TODO: replace this
    lengths = [len(words(s)) for s in sentences(text)] # 对每个句子 s，数一下它有几个词，把结果收集成一个列表
    if len(lengths) < 2: # 只有一句话时，没有"变化"可言，而且 statistics.stdev 遇到少于 2 个值会报错（docstring 里专门提醒过）。先返回 0.0，后面在 style_signal 里决定怎么处理
        return 0.0       # 没有句子，是[],len是0 ； 一句话，是[15],len是1；两句话len是2；所以是小于2
    return statistics.stdev(lengths) / statistics.mean(lengths)
# stdev / mean：标准差 ÷ 平均值，叫变异系数（coefficient of variation）
# 标准差：数字之间差别有多大。[10, 12, 11, 10] 很小，[11, 24, 4, 4] 很大
# 为什么要除以平均值：一篇平均每句 30 词的文章，标准差天然比平均每句 8 词的大。除以平均值，长句文章和短句文章才能放在一起比较
# 方向：数值越小 → 句子越整齐 → 越像 AI

# 指标2：用词多样性
def type_token_ratio(text: str) -> float:
    """
    Unique words over total words. ← TODO

    Returns:
        A float between 0 and 1. Higher means more varied vocabulary.

    Worth knowing before you rely on it: this measure falls as text gets
    longer, because common words repeat. Two texts of different lengths aren't
    directly comparable on it, and if your test inputs vary a lot in length,
    that alone can look like a signal.
    """
    # TODO: replace this
    tokens = words(text)
    if not tokens: # 没有词时，返回 0.0，后面在 style_signal 里决定怎么处理
        return 0.0
    return len(set(tokens)) / len(tokens) # set() 去重，len(set(...)) 是独特词的数量，len(tokens) 是总词数
# 方向：数值越小 → 重复越多 → 越像 AI
# 但是注意 M1 发现的问题：文本越长，这个值天然越低

# 指标3：标点密度
def punctuation_density(text: str) -> float:
    """
    How much punctuation, relative to length. ← TODO

    Returns:
        A float. Whether you count all punctuation or only some kinds — commas,
        semicolons, dashes — is a real choice. Semicolons and em dashes are
        more interesting than full stops, because they vary more between
        writers.
    """
    # TODO: replace this
    tokens = words(text)
    if not tokens: # 没有词时，返回 0.0，后面在 style_signal 里决定怎么处理
        return 0.0
    marks = re.findall(r"[,;:()!?\u2014\u2013]", text) # 只算逗号、分号、冒号、括号、问号、感叹号、长破折号（—）和短破折号（–），不算句号; 为什么不算句号：每句话都有句号，没有区分度。docstring 里说过，分号和破折号更能体现个人习惯
    return len(marks) / len(tokens) # 标点数 ÷ 词数
# 方向：暂时不确定！ AI 写作常用很多逗号，ChatGPT 还特别爱用长破折号 —；但人写作也会用。这个方向要看数据再决定。


# ── Combining them ───────────────────────────────────────────────────────────

def style_signal(text: str) -> float:
    """
    The style signal as a 0–1 score. **Higher means more likely AI.** ← TODO

    Combine your three measures into one number. Same direction as
    `detector.model_signal`, so that `scoring.combine_signals` can treat them
    the same way — if one of your signals runs backwards, everything above it
    is wrong in a way that's hard to see.

    Two things to decide and write down:

      1. Which direction each measure points. Low spread means more AI-ish, so
         it needs flipping. Work out which of your three need that.
      2. How to get each onto a comparable scale. A raw type-token ratio sits
         between 0 and 1; a raw punctuation count doesn't. Adding them
         unscaled means whichever has the bigger numbers wins by default.

    Test it on the four calibration inputs from Milestone 4 — clearly AI,
    clearly human, plain conventional human writing, lightly-edited AI — before
    you trust it. Plain and ordinary, not formal: formal prose reads as *human*
    to signal one, and it is plain writing that gets accused.
    """
    # TODO: replace this
    if len(sentences(text)) < 3:  # 原来是少于三句话时，return 0.5, 在M5时决定调整，笔记中选择的修复方案2
        return None
    length = [len(words(s)) for s in sentences(text)]
    if sum(length) == 0: # 新增：一个能数的词都没有
        return None      # 不再往下走到除以零
    # Only spread is used. TTR and punctuation overlapped between AI and my own
    # writing in round 3 (see README Calibration Log), so they get weight 0.
    spread = sentence_length_spread(text)
    SPREAD_AI = 0.1
    SPREAD_HUMAN = 0.6
    score = (SPREAD_HUMAN - spread) / (SPREAD_HUMAN - SPREAD_AI)
    return round(min(max(score, 0.0), 1.0), 4)



if __name__ == "__main__":
    import sys

    text = " ".join(sys.argv[1:]) or (
        "The system works well. It handles most cases correctly and provides "
        "good results. Users generally find it easy to use and understand."
    )

    print(f"{len(sentences(text))} sentences, {len(words(text))} words\n")
    print(f"sentence_length_spread   {sentence_length_spread(text)}")
    print(f"type_token_ratio         {type_token_ratio(text)}")
    print(f"punctuation_density      {punctuation_density(text)}")
    print(f"style_signal             {style_signal(text)}   (higher = more likely AI)")
    print("\nAll zeros? These are stubs — Milestone 4 is where you build them.")
