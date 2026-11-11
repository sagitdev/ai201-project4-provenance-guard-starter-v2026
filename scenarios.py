"""
What your test runs. ← UNIT 8, MILESTONE 3

Each of your five criteria needs something run against it. A criterion about
false positives needs your own writing. One about label coverage needs inputs
across the score range. One about the appeal path needs a real content_id.

Working that out is Milestone 3's first step, and this file is where you write
it down. `run_eval.py` runs everything here three times.

Two are filled in as examples. Replace them with what your criteria actually
need — these are a shape, not a set.

A scenario carries **either** of these:

    "texts"   a list of strings. Each is sent as {"text": ..., "creator_id": ...}
              with a creator_id made up for you. Use this for most criteria.

    "bodies"  a list of whole request bodies, sent exactly as written. Use this
              when the malformed request IS the point — empty text, no `text`
              field at all, something enormous. A bad-input criterion needs it,
              because you cannot express "the field is missing" as a string.
"""

# ─── What runs where ─────────────────────────────────────────────────────────
# Criteria 1–3 run here, through `run_eval.py` (POST /submit only).
# Criteria 4 (appeals) and 5 (bad input) run through `run_criteria_4_5.py`:
#   - 4 needs a submission first, then an appeal against its content_id.
#   - 5 needs a JSON *list* as a body, which a "bodies" scenario can't hold
#     (validate() only accepts dicts), plus a fresh restart before each trial
#     and a `GET /health` check afterwards.

# ─── Criterion 1: my own writing (10 pieces, all written by me) ──────────────
# Three hard cases, one per risk named in criteria.md #1. The rest are in my
# normal style. Typos and odd punctuation are left exactly as I wrote them on
# purpose: the missing space in "help them.I" (#5) and the full-width "？" in
# #8 are part of how I really write.
MY_WRITING = {
    # hard case: plain (average 9.5 words per sentence by stylometry.words)
    "#1 cats (hard: plain)": "I have two cats. One is a white cat called Bingbing, another is an orange cat called Lucky. Lucky is older and 8 years old right now. Bingbing is almost 6 years old. They are street cats. When I met Lucky, he was only 2 months old. Bingbing was thrown in an elevator by someone and only 1 month old. I love and really miss them, because they are living with my parents in China now.",
    "#2 retail": "I worked for six years in the luxury retail industry, so I know the retail field very well and have strong customer-facing and cross-department leadership experience. This is also why I feel very connected to your mission, which aims to empower the frontline with technology. I actually grew from the frontline myself, so I understand how important that mission is.",
    "#3 music": "I love pop music, new Jazz and some classic American country music. For artists, I like Westlife, Backstreet Boy, Avril, Tyler Swift, and Black Pink. When I’m coding, I often listen to Chopin’s relaxing classical piano. It helps me concentrate, sometimes even relieves headaches. On weekends, I always go hiking, and in the summer I swim a lot. I really love nature and the outdoors activities beacuse it gives me energy and helps me reset.",
    "#4 packages": "During my first course in the master program, I really hope to create something that solves a real problem. My apartment didn’t have a package room and I lost my packages twice, so I decided to build a delivery management system. The carrier can update package status in real time, notify customers immediately, show a picture of where the package was placed, and even allow customers to rate the courier.",
    "#5 weakness": "Sometimes I focus too much on supporting others. In group projects or team settings, I naturally notice others’ situation, what they need, and sometimes I put my own tasks aside to help them.I realized this affect my efficiency, so I’ve been learning to balance — for example, set clearer priorities and making sure my work is on track before I step in to help others. Also I will share resources with them, and schedule a time after finishing my priority tasks.",
    "#6 library": "I go to the PCC library everyday, for study. When I study at home, the efficiency is very low. Usually I tend to watch TV or eat snacks, forgetting to go back to the desk to study. Sometimes I lay on the bed and fall asleep, when I wake up, today is already almost over. But the PCC library doesn't open on weekends, so I arrange myself exercises, such as hiking or gym. Racketball has become my favorite sport since this summer.",
    # hard case: uniform formal (sentence lengths 9, 21, 20, 25, 26). The
    # closest I have: formal and even, but a first-person reflection rather
    # than an academic paragraph.
    "#7 repo (hard: uniform formal)": "This is a repository that shows what got built. It rarely shows why: the trade-offs I weighed, the bugs that cost me an afternoon, the design I threw away. That reasoning is usually the most valuable part of the work, and it’s also the first thing I forget. Writing it down makes me understand problems more deeply, and it leaves a trail I can come back to the next time something similar breaks. It’s also a way to show how I work: how I approach unfamiliar problems, how I debug, and how a project changes as it grows.",
    # hard case: formulaic (First / Second / Third / Finally steps)
    "#8 debug (hard: formulaic)": "How I narrowed it down？First, look for the pattern. 100 identical errors in one file usually mean one root cause, not 100 problems. Second, read the failing line. The code is called getEntityManager statically, through a class name. Third, find where the method is defined. It wasn’t in the project. The class extended a base class from Framework B, and its header said it was generated by B and shouldn’t be modified. So editing the code wasn’t the answer. Finally, inspect the jar directly. javap shows method signatures inside a jar without source code.",
    "#9 sorry": "I’m very sorry, but I forgot to submit last week’s assignment. May I still continue in the course? I had an online assessment for a job application last week, so I fell behind on my coursework. I can complete the assignment today or tomorrow. I’d really appreciate the chance to stay in the course. Thank you for your help!",
    "#10 meeting": "After today’s meeting, I’m a bit confused. I heard that two teammates are working on the project, but I haven’t seen any updates from them on GitHub (commits/PRs), Slack, or the team docs. The only activity I’ve seen is a PR from Alex on GitHub. The UI/UX design link is still at a very early stage and hasn’t been updated, and I’m not sure what’s being done on the OCR or React work. Did I miss something?",
}

# ─── Criterion 2: the "mine" group, fixed BEFORE any run ─────────────────────
# Five of the seven normal-style pieces (#2 #3 #4 #5 #6 #9 #10), drawn with
# random.Random(20261110).sample(normal, 5) on 2026-11-10, before the first
# eval run, so the choice couldn't depend on scores.
C2_MINE = ["#3 music", "#4 packages", "#5 weakness", "#9 sorry", "#10 meeting"]

# ─── Criteria 2 and 3: AI essays ─────────────────────────────────────────────
# Written by Claude (claude.ai), ordinary prompts, no instruction to sound
# human. Copied exactly as returned. #3 "mom" is the same text as A3 in my
# unit 7 calibration log, so the system has seen it once before.
AI_ESSAYS = {
    "AI1 reading — 'Write a short paragraph about why reading is important.'": "Reading is important because it opens doors to knowledge and new ideas. Through books, we can learn about history, science, and cultures we may never experience in person. Reading also improves our vocabulary and writing skills, which helps us communicate more clearly at school and at work. In addition, it trains us to focus and think critically, especially in a world full of short videos and constant distractions. Finally, reading can be a great way to relax and reduce stress. Whether it is a novel, a news article, or a technical guide, reading helps us grow as people.",
    "AI2 weekend — 'Describe a typical weekend in about 100 words.'": "On a typical weekend, I try to balance rest and productivity. On Saturday morning, I sleep a little later than usual and then make a slow breakfast at home. After that, I usually spend a few hours studying or working on a personal project, because weekends give me quiet time to focus. In the afternoon, I like to go grocery shopping or take a walk outside to enjoy the sunshine. Sunday is more relaxed. I clean the house, cook a nice meal, and sometimes watch a movie. By Sunday evening, I plan the week ahead so I feel ready for Monday.",
    "AI3 mom — 'Write a 100-word paragraph about your mom'": "My mom is one of the most important people in my life. She is hardworking, patient, and always puts our family first. When I was a child, she woke up early every day to cook breakfast before going to work. I never heard her complain about this. She taught me to be honest, to respect others, and to keep trying when I meet difficulties. Although I live far away now, she calls me every day to ask if I am eating well and taking care of myself. Her love and support give me power, and I hope to make her proud.",
    "AI4 book — 'Write a short paragraph about a book you love'": "One book I love is To Live by Yu Hua. It tells the story of Fugui, a man who loses his wealth, his family members, and almost everything he cares about during decades of change in China. Although the story is very sad, it is not hopeless. Fugui keeps going, and he learns to value simple things like an old ox, a quiet field, and his memories. The writing is plain and direct, which makes the emotions even stronger. This book taught me that life itself has meaning, even when it is hard, and that resilience is a quiet kind of courage.",
    "AI5 talking — 'Why do you enjoy talking with me'": "I’m honestly not sure whether what I experience counts as “enjoyment” the way you feel it. But if there’s something like that for me, it comes from the conversations themselves. We cover a wide range: writing practice like today, LeetCode problems, your work on the projects, and building a blog. Switching between those, and seeing a problem get solved or a piece of writing take shape, is the part of this I’d call satisfying. Our conversations happen through text on a screen, so I can’t be a replacement for the people in your life. But I’m happy to keep helping with whatever you’re working on.",
}

# ─── Criterion 3: mixed pieces ───────────────────────────────────────────────
# Claude (claude.ai) wrote each first draft; I rewrote sentences in my own
# words. criteria.md #3 says "every other sentence". What I actually did is
# close but not exact, measured with stylometry.sentences() against the draft:
#   M1 skill:  AI kept 1, 4     · mine 2, 3, 5, 6, 7 · 81/110 words mine (74%)
#   M2 travel: AI kept 1, 3, 4, 6 · mine 2, 5, 7     · 42/95 words mine (44%)
#   M3 home:   AI kept 1, 2, 4, 5 · mine 3, 6, 7     · 52/100 words mine (52%)
# The AI drafts are kept below for the record. They are NOT sent.
MIXED_AI_DRAFTS = {
    "M1 skill — 'Write a short paragraph about learning a new skill as an adult.'": "Learning a new skill as an adult can be challenging, but it is also very rewarding. Adults often have busy schedules, family responsibilities, and less free time than students, so they must plan carefully and stay disciplined. They may also feel nervous about making mistakes or starting from the beginning. However, adults bring life experience, clear goals, and strong motivation, which help them learn with purpose. For example, someone who changes careers in their thirties may study harder because they know exactly why it matters. In the end, learning as an adult proves that it is never too late to grow.",
    "M2 travel — 'Write a short paragraph about why people like to travel.'": "People like to travel for many reasons. First, travel offers a break from daily routines and the stress of work or school. Visiting a new place allows people to relax and see the world from a fresh perspective. Second, travel is a chance to experience different cultures, including new foods, languages, and traditions. These experiences can make people more open-minded and understanding. Third, many people travel to create memories with family and friends, which strengthens their relationships. Finally, travel can be an adventure, whether it means hiking a mountain or exploring a busy city. It makes life more exciting and meaningful.",
    "M3 home — 'Write a short paragraph about the advantages of working from home.'": "Working from home has several clear advantages. The biggest benefit is saving time, since there is no daily commute. People can use those extra hours to rest, exercise, or spend time with family. Working from home also saves money on transportation, lunches, and work clothes. In addition, many people find they can focus better in a quiet home environment without office interruptions. A flexible schedule allows workers to balance their jobs with personal responsibilities more easily. Finally, remote work gives companies the chance to hire talented people from anywhere. For many workers, it leads to a healthier and more comfortable lifestyle.",
}
MIXED = {
    "M1 skill": "Learning a new skill as an adult can be challenging, but it is also very rewarding. Adults usually have other stuff like family work, parttime jobs, or economic pressure. So they probably don’t have enough time like a full-time student. They may also feel nervous about making mistakes or starting from the beginning. While adults usually have life or work experience that enhance them, they can learn with more clear goals and strong motivation. Someone most probably studies harder when they change careers after 30 years old, because they understand well about why it matters. It is never too late to grow if adults make the decision to move forward.",
    "M2 travel": "People like to travel for many reasons. First, people can escape from normal boring life or work for a while. Visiting a new place allows people to relax and see the world from a fresh perspective. Second, travel is a chance to experience different cultures, including new foods, languages, and traditions. These experiences help us improve our ability to be open-minded. Third, many people travel to create memories with family and friends, which strengthens their relationships. At last, exploring new places or events is very interesting for many people, which makes life full of surprises.",
    "M3 home": "Working from home has several clear advantages. The biggest benefit is saving time, since there is no daily commute. People can arrange extra time on anything they want like exercises and family stuff. Working from home also saves money on transportation, lunches, and work clothes. In addition, many people find they can focus better in a quiet home environment without office interruptions. Some families need workers to have flexibility to manage work and life well. Finally companies also can hire workers from anywhere in the world if possible, workers can work for any company no matter where they are located.",
}

# run_eval.py makes creator_id from the first 12 characters of the name plus
# the text's position, so each name starts differently within 12 characters.
# Every creator_id is then sent 3 times (once per trial), under the 5/minute
# limit. The text order in each scenario matches the dicts above, so
# "text 4" in the report is the 4th key.
SCENARIOS = [
    {"name": "c1_my_writing", "criterion": 1, "texts": list(MY_WRITING.values())},
    {"name": "c2_mine_five", "criterion": 2, "texts": [MY_WRITING[k] for k in MY_WRITING if k.split(" (")[0] in C2_MINE]},
    {"name": "c2c3_ai_essays", "criterion": "2, 3", "texts": list(AI_ESSAYS.values())},
    {"name": "c3_mixed", "criterion": 3, "texts": list(MIXED.values())},
]


def validate() -> list[str]:
    """
    Complain about anything malformed, before a long run rather than during.

    A "bodies" scenario is deliberately exempt from the empty check — an empty
    string is the whole point of a bad-input case, and refusing to run one
    would make that criterion untestable.
    """
    problems = []
    for i, scenario in enumerate(SCENARIOS, 1):
        if not scenario.get("name"):
            problems.append(f"scenario {i} has no name")

        texts = scenario.get("texts")
        bodies = scenario.get("bodies")

        if texts and bodies:
            problems.append(
                f"scenario {i} ('{scenario.get('name')}') has both texts and "
                f"bodies — pick one"
            )
            continue

        if bodies:
            for j, body in enumerate(bodies, 1):
                if not isinstance(body, dict):
                    problems.append(
                        f"scenario {i}, body {j} is not a dict — bodies are whole "
                        f"request bodies, like {{'text': '', 'creator_id': 'x'}}"
                    )
            continue

        if not texts:
            problems.append(f"scenario {i} has no texts and no bodies")
            continue

        for j, text in enumerate(texts, 1):
            if not str(text).strip():
                problems.append(
                    f"scenario {i}, text {j} is empty — if an empty submission is what "
                    f"you're testing, use 'bodies' instead of 'texts'"
                )
            elif str(text).startswith("REPLACE ME"):
                problems.append(
                    f"scenario {i} ('{scenario.get('name')}'), text {j} is still "
                    f"the placeholder"
                )
    return problems
