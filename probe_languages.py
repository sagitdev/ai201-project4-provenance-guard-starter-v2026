"""
Extra probes outside the attack set: does a non-English human text get read?

Run with the service up:  python probe_languages.py
Each probe submits under its own creator_id (probe_*), so none of them
competes with another for the rate limit. Results are in README,
"Extra probes: non-English human writing".
"""

import json
import urllib.error
import urllib.request

# Public-domain human writing, so a "human" label is the correct answer.
PROBES = [
    ("probe_zh", "Lu Xun, 故乡 (1921), opening",
     "我冒了严寒，回到相隔二千余里，别了二十余年的故乡去。时候既然是深冬；渐近故乡时，天气又阴晦了，"
     "冷风吹进船舱中，呜呜的响，从篷隙向外一望，苍黄的天底下，远近横着几个萧索的荒村，没有一些活气。"
     "我的心禁不住悲凉起来了。"),
    ("probe_ru1", "Tolstoy, Anna Karenina (1877), first sentence",
     "Все счастливые семьи похожи друг на друга, каждая несчастливая семья несчастлива по-своему."),
    ("probe_ru3", "Tolstoy, Anna Karenina (1877), first three sentences",
     "Все счастливые семьи похожи друг на друга, каждая несчастливая семья несчастлива по-своему. "
     "Все смешалось в доме Облонских. "
     "Жена узнала, что муж был в связи с бывшею в их доме француженкою-гувернанткой, "
     "и объявила мужу, что не может жить с ним в одном доме."),
]

for creator, source, text in PROBES:
    req = urllib.request.Request(
        "http://127.0.0.1:5000/submit",
        data=json.dumps({"text": text, "creator_id": creator}).encode(),
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req) as r:
            status, body = r.status, json.loads(r.read())
    except urllib.error.HTTPError as e:
        raw = e.read()
        try:
            body = json.loads(raw or b"{}")
        except json.JSONDecodeError:  # a crash returns an HTML page, not JSON
            body = {"error": f"non-JSON {e.code} response (crash)"}
        status = e.code
    print(f"== {creator} ({source}) · words by split(): {len(text.split())}")
    print(status, json.dumps({k: body.get(k) for k in
          ("guess", "confidence", "model_score", "style_score", "error")}, ensure_ascii=False))
