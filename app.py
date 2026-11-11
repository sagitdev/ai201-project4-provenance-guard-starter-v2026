#!/usr/bin/env python3
"""
Provenance Guard — the web service.

    python app.py

Then, in another terminal:

    curl -X POST http://127.0.0.1:5000/ping \
      -H "Content-Type: application/json" \
      -d '{"message": "hello"}'

That's the example route. It works right now, before you've written anything.
**Leave it alone** — it's your control. When something breaks later, check that
`/ping` still answers: if it does, the problem is in your handler; if it
doesn't, it's the service itself.

Routes:

    POST /ping        the worked example. Already works. Don't edit it
    POST /submit      ← YOU BUILD THIS (Milestone 3, 4, 5)
    POST /appeal      ← YOU BUILD THIS (Milestone 5)
    GET  /log         the audit log. Already works
    GET  /health      is the service up, and is the model loaded
"""

import uuid

from flask import Flask, jsonify, request

import audit
import config

import detector
import scoring
import stylometry
# import 会不会让模型一启动就加载？不会。 看 detector.py：模型只在第一次调用 _load() 时才加载（这叫懒加载 lazy loading）。import 只是让 app.py "认识" detector 这个模块。这一点对第 5 条标准很重要：坏请求在调用 model_signal 之前就被拒绝，detector_loaded 就会一直是 false。

app = Flask(__name__)


def usable_creator_id(value):
    """
    The creator_id if it's safe to log, otherwise None.

    creator_id 是调用方自己填的，所以写进日志前要检查：必须是非空字符串，并且不超过
    MAX_CREATOR_ID_CHARS。不合格时返回 None（日志里是 null）：
    - 不用 "unknown"：用户可以真的把 creator_id 写成 "unknown"。
    - 不截断：截断后的字符串可能正好是另一个真实用户的 id。
    /submit、/appeal 和限流都用这一个函数，规则只写一遍。
    """
    if not isinstance(value, str) or not value.strip():
        return None
    if len(value) > config.MAX_CREATOR_ID_CHARS:
        return None
    return value


# ── Rate limiting — UNIT 8 ────────────────────────────────────────────────────
# Off until you turn it on. In unit 8, Milestone 1:
#
#   1. Set RATE_LIMITING_ENABLED = True in config.py (or AI201_RATE_LIMITS=1)
#   2. Choose your numbers there
#   3. Uncomment the @limiter.limit(...) line on /submit below
#
# The order doesn't matter. While limiting is off, that decorator is a no-op
# that quietly does nothing, so uncommenting it early costs you nothing — but
# it also means no 429 until you've done step 1.
#
# The storage backend is preconfigured, which stops Flask-Limiter printing a
# warning on every start. In-memory is right for one laptop and wrong for
# anything real — a restart forgets every count.

class _LimiterOff:
    """
    Stands in for the real limiter while rate limiting is off.

    It makes @limiter.limit(...) a decorator that returns the route
    untouched, so uncommenting the line before you flip the setting is
    harmless instead of a crash on startup.
    """

    def limit(self, *args, **kwargs):
        return lambda view: view


limiter = _LimiterOff()
if config.RATE_LIMITING_ENABLED:
    from flask_limiter import Limiter
    from flask_limiter.util import get_remote_address

    def rate_limit_key():
        """
        Who a request counts against.

        Falling back to the caller's address is the easy version. Unit 8's
        stretch asks about per-creator limits instead — and the difference
        matters: one script can look like a thousand callers, and one household
        can look like one.
        """
        payload = request.get_json(silent=True)
        # A body that parses as JSON but isn't an object — a bare list or
        # string — has no .get. Without this guard the key function raises
        # BEFORE the route runs, and a malformed request becomes a 500 that
        # looks like your handler crashed when your handler never ran.
        if not isinstance(payload, dict):
            return get_remote_address()
        # 超长的 creator_id 也退回到按 IP 计数，不拿它当限流的 key 存进内存。
        return usable_creator_id(payload.get("creator_id")) or get_remote_address()

    limiter = Limiter(
        key_func=rate_limit_key,
        app=app,
        storage_uri=config.RATE_LIMIT_STORAGE,
        default_limits=[],
    )

    @app.errorhandler(429)
    def rate_limited(exc):
        """
        A rejected request still leaves a trace.

        ⚠️ An attack that shows up only as an absence is one you'll never find.
        """
        payload = request.get_json(silent=True)
        if not isinstance(payload, dict):
            payload = {}
        audit.log_rejection(
            # 和 reject() 一样，不合法或超长的 creator_id 记成 None。
            creator_id=usable_creator_id(payload.get("creator_id")),
            reason="rate_limited",
            limit=str(exc.description),
        )
        return jsonify({
            "error": "rate_limited",
            "message": "Too many submissions. Try again shortly.",
            "limit": str(exc.description),
        }), 429


# ── The worked example. Already works. Don't edit. ────────────────────────────

#装饰器：@app.post("/ping") 写在函数上方，意思是"收到 POST /ping 请求时，调用下面这个函数"。
@app.post("/ping")
def ping():
    """
    Everything a route needs, in six lines.

    JSON arrives as a dict. You pull things out of it. You return a dict and
    the framework turns it into a response. That's the whole idea.
    """
    payload = request.get_json(silent=True) or {}
    return jsonify({
        "ok": True,
        "you_sent": payload.get("message"),
        "service": "provenance-guard",
    })


@app.get("/health") # 报告服务是否在线、模型是否已加载、限流是否开启、日志有多少条。
def health():
    """Is the service up, and has the model been downloaded yet?"""
    import detector

    loaded = detector._model is not None
    return jsonify({
        "ok": True,
        "detector_model": config.DETECTOR_MODEL,
        "detector_loaded": loaded,
        "rate_limiting": config.RATE_LIMITING_ENABLED,
        "log_entries": len(audit.read_entries()),
    })


# ── YOU BUILD THIS ────────────────────────────────────────────────────────────
def reject(error, message, creator_id=None, status=400):
    # creator_id 默认 None（日志里是 null）：真正的 creator_id 一定是非空字符串，永远不会是 null，
    # 所以"没填"和"某个用户真叫 unknown"不会混在一起。
    """
    A malformed request is a rejection, not a crash.

    The route should never raise an exception on a bad request. That looks like
    a broken service to the caller, and it looks like a broken route to you.
    """
    # endpoint 记下是哪个路由拒绝的。/submit 和 /appeal 都会出现 invalid_json 这类错误，
    # 不写的话，Unit 8 读日志时分不清是谁拒绝的。request.path 由 Flask 自动提供，调用的地方不用改。
    audit.log_rejection(creator_id=creator_id, reason=error, endpoint=request.path)
    return jsonify({
        "error": error,
        "message": message,
    }), status

@app.post("/submit")
@limiter.limit(f"{config.RATE_LIMIT_PER_MINUTE}/minute;{config.RATE_LIMIT_PER_DAY}/day")
def submit():
    """
    Take a piece of text, decide about it, log the decision, answer.
    ← TODO — Milestones 3, 4 and 5

    Expects JSON:
        {"text": "...", "creator_id": "..."}

    Should return JSON with, at minimum:
        {"content_id": "...", "guess": "...", "confidence": 0.0, "label": "...",
         "model_score": 0.0, "style_score": 0.0}

    ⚠️ **Both signal scores go in the response, not just the log.** Unit 8's
    `run_attacks.py` and `run_eval.py` read `model_score` and `style_score`
    straight off this response and put them in your reports. Leave them out and
    every row of next unit's evidence says `null` — which is exactly the
    diagnostic you need to name a stage and a mechanism. You do not want to
    find that out after running the attack set.

    ─────────────────────────────────────────────────────────────────────────
    Build it in three passes. Do not skip ahead — the ordering is how you tell
    a broken route from a broken signal.

    **Milestone 3 — the route answers.**
      1. Return a hardcoded response. Confirm `curl` gets it back before you
         add any logic at all.
      2. Then pull `text` and `creator_id` out of the payload.
      3. Then call ONE signal — `detector.model_signal(text)` — and put the
         real number in. Leave confidence and label as placeholders.
      4. Log every submission with `audit.log_decision(...)`. The content_id
         matters: `/appeal` needs it, and a student who skips it rebuilds this
         whole flow later.

    **Milestone 4 — the second signal and the score.**
      5. Add `stylometry.style_signal(text)`.
      6. Combine them with `scoring.combine_signals(...)`.
      7. Log BOTH signal scores alongside the combined one, and put them in the
         response too. Next unit you can't diagnose anything without them.

    **Milestone 5 — the label.**
      8. `scoring.score_to_label(...)` and put the real label in the response.

    ─────────────────────────────────────────────────────────────────────────
    Worth deciding early, because unit 8's attack set will decide it for you:
    what should this do when `text` is missing, empty, or enormous? A crash on
    a malformed input is one of the most common real failures there is.
    """
    payload = request.get_json(silent=True)
    # 去掉了 or {} 加了 or {}，坏 JSON 会悄悄变成空字典 {}，后面只会报"缺 text"，看不出真正的原因是 JSON 格式错了。去掉以后，坏 JSON 得到 None，就能返回准确的 invalid_json。

    if not isinstance(payload, dict): #意思是"payload 是不是一个字典"。能同时挡住 3 种情况：不是 JSON（None）、JSON 是列表（["a"]）、JSON 是字符串（"hello"）。M1 Task 1 里提到过，列表没有 .get()，不挡住就会崩溃变成 500。
        return reject("invalid_json", "Please send a JSON object with text and creator_id.")

    creator_id = payload.get("creator_id")
    if not isinstance(creator_id,str) or not creator_id.strip():
        return reject("creator_id_missing","Please include a creator_id saying who wrote this.")
    # creator_id 会写进每一条日志，超长时拒绝，并且日志里记成 None（reject 的默认值），不写原文。
    if len(creator_id) > config.MAX_CREATOR_ID_CHARS:
        return reject(
            "creator_id_too_long",
            f"Please keep your creator_id under {config.MAX_CREATOR_ID_CHARS} characters.",
        )

    text = payload.get("text")
    if not isinstance(text, str): #同时挡住"没有 text"（None）、text: null（None）、text: 123（数字）
        return reject("text_missing", "Please include the text you'd like us to read.", creator_id)
    if not text.strip(): # .strip() 去掉开头和结尾的空格、换行。只有空格的文字 strip 之后是 ""，not "" 为真，于是被拒绝。
        return reject("text_empty", "The text is empty. Please paste in your writing.", creator_id)
    if len(text) > config.MAX_TEXT_CHARS:
        return reject(
            "text_too_long",
            f"Please keep submissions under {config.MAX_TEXT_CHARS:,} characters.", # 这叫 f-string：字符串前面加 f，{} 里的变量会被替换成它的值。:, 表示加千位分隔符，显示成 50,000。
            creator_id,
        )
    if len(text.split()) < config.MIN_TEXT_WORDS:
        return reject(
            "text_too_short",
            "Please submit at least a few sentences so we can read it properly.",
            creator_id,
        )

    content_id = str(uuid.uuid4())# uuid4() 生成一个随机编号，str() 把它变成字符串，JSON 只认字符串。
    model_score = detector.model_signal(text)
    style_score = stylometry.style_signal(text)   
# 现在坏请求会写日志，但正常请求不会：判定做完就返回了，没留下记录。第 4 步要补上这一条。
# 为什么重要： 下一步的 /appeal 要用 audit.entries_for(content_id) 去日志里查找这个 content_id。正常请求不写日志的话，所有申诉都会返回 404。
    confidence = scoring.combine_signals(model_score, style_score)
    guess,label = scoring.score_to_label(confidence)
 # milestone 4
    audit.log_decision(
        content_id = content_id,
        creator_id = creator_id,
        guess = guess,
        model_score = model_score,
        style_score = style_score,
        combined_score = confidence,
        label = label,
    )

    return jsonify({
        "content_id": content_id,
        "guess": guess,        
        "confidence": confidence, 
        "label": label,  
        "model_score": model_score,
        "style_score": style_score,     
    })


@app.post("/appeal")
def appeal():
    """
    A writer says you got it wrong. ← TODO — Milestone 5

    Expects JSON:
        {"content_id": "...", "reasoning": "..."}

    Should:
      1. Check the content_id actually exists — `audit.entries_for(id)` tells
         you. A typo here fails silently and looks like a broken endpoint,
         which is the single most common way this milestone eats an hour.
      2. Record the appeal with `audit.log_appeal(...)`, which moves the item
         to `under_review`.
      3. Confirm to the writer. No automatic re-checking needed.

    This is the smallest endpoint in the project and the one that matters most
    to the person on the other end. It's the only thing standing between a
    wrong accusation and nothing at all.
    """
    payload = request.get_json(silent=True)
    # 和 /submit 一样不加 or {}：坏 JSON 得到 None，才能返回准确的 invalid_json。
    if not isinstance(payload, dict):
        return reject("invalid_json", "Please send a JSON object with content_id, creator_id, reasoning and attestation.")

    # 先检查格式（400），再查日志（404 / 403）。格式不对的请求不用去读日志。
    content_id = payload.get("content_id")
    creator_id = payload.get("creator_id")
    reasoning = payload.get("reasoning")
    attestation = payload.get("attestation")

    # creator_id 先取出来，后面每条拒绝记录都能写上是谁发的。
    # 不合法或超长时是 None（日志里是 null），规则见 usable_creator_id。
    who = usable_creator_id(creator_id)

    if not isinstance(content_id, str) or not content_id.strip():
        return reject("content_id_missing", "Please include the content_id of the result you're appealing.", who)
    if not isinstance(creator_id, str) or not creator_id.strip():
        return reject("creator_id_missing", "Please include your creator_id so we know this is your work.")
    if who is None:
        # 走到这里说明 creator_id 是非空字符串，只是太长。
        return reject(
            "creator_id_too_long",
            f"Please keep your creator_id under {config.MAX_CREATOR_ID_CHARS} characters.",
        )
    if not isinstance(reasoning, str) or not reasoning.strip():
        return reject("reasoning_missing", "Please tell us why you think this result is wrong.", who)
    # reasoning 会完整写进日志，不设上限的话，反复发超长申诉会让日志一直变大。
    # 先 strip 再量长度，和写进日志的内容保持一致。
    if len(reasoning.strip()) > config.MAX_REASONING_CHARS:
        return reject(
            "reasoning_too_long",
            f"Please keep your reason under {config.MAX_REASONING_CHARS:,} characters.",
            who,
        )
    # 必须是布尔值 True：字符串 "true"、数字 1 都不算。勾选框就是 true / false。
    if attestation is not True:
        return reject("attestation_required", "Please confirm this is your own work to submit an appeal.", who)

    content_id = content_id.strip()
    # 只认 /submit 写下的那条判定记录（status == "decided"）。
    # 之前的申诉记录也带 content_id，但它不是"原始提交"，不能用来核对作者。
    decisions = [e for e in audit.entries_for(content_id) if e.get("status") == "decided"]
    if not decisions:
        return reject(
            "content_not_found",
            "We couldn't find a result with that content_id. Please check it and try again.",
            who,
            status=404,
        )

    original = decisions[0]
    if original.get("creator_id") != creator_id:
        return reject(
            "not_your_content",
            "You can only appeal results for your own submissions.",
            who,
            status=403,
        )

    # 只追加，不改原来的 decided 记录：日志里能看到"先判定、后被申诉"的顺序。
    audit.log_appeal(content_id=content_id, creator_id=creator_id, reasoning=reasoning.strip())

    # 用 "received" 而不是 "successful"：还没有人做出决定，不能让写作者以为已经赢了。
    return jsonify({
        "content_id": content_id,
        "status": "under_review",
        "message": "We've received your appeal. A person will review it.",
    })


# ── Already works ─────────────────────────────────────────────────────────────

@app.get("/log")
def get_log():
    """
    The audit log, most recent last.

        curl "http://127.0.0.1:5000/log?limit=10"

    You need this in unit 8 to paste entries into your README, and you need it
    now to see whether your logging is actually working.
    """
    limit = request.args.get("limit", type=int)
    entries = audit.read_entries(limit=limit)
    return jsonify({"count": len(entries), "entries": entries})


def main():
    print(f"Provenance Guard on http://{config.HOST}:{config.PORT}")
    print(f"  detector model:  {config.DETECTOR_MODEL}")
    print(f"  rate limiting:   {'ON' if config.RATE_LIMITING_ENABLED else 'off (unit 8)'}")
    print(f"  audit log:       {config.AUDIT_LOG}")
    print()
    print("Check it's alive:")
    print(f'  curl -X POST http://{config.HOST}:{config.PORT}/ping \\')
    print('    -H "Content-Type: application/json" \\')
    print("    -d '{\"message\": \"hello\"}'")
    print()
    # debug=True hands out an interactive debugger, so it's local-only — see config.py
    app.run(host=config.HOST, port=config.PORT, debug=config.DEBUG)


if __name__ == "__main__":
    main()
