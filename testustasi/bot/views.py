"""The bot's screens as (html, rows of buttons). demo/bot-views.js is a line-by-line port, so the simulated bot in the
browser demo reads and behaves exactly like this one (the same texts, buttons and callback data). A button is
{"text", "data"} (a callback), {"text", "app": "?t=5"} (opens the Mini App there) or {"text", "url"}."""

from __future__ import annotations

from ..core import analysis as A
from ..core.text import short
from ..i18n import Raw, minutes, num, pct, questions, students, t, when


def btn(text: str, data: str) -> dict:
    return {"text": text, "data": data}


def app(text: str, where: str = "") -> dict:
    return {"text": text, "app": where}


def back(lang: str, data: str = "m") -> list[dict]:
    return [btn(t(lang, "btn.back"), data)]


def hello(lang: str) -> tuple:
    return t(lang, "bot.hello"), [[btn(t(lang, "btn.teacher"), "role:t")], [btn(t(lang, "btn.student"), "role:s")], [btn(t(lang, "btn.lang"), "lang")]]


def menu_teacher(lang: str, name: str, classes: int, tests: int) -> tuple:
    return t(lang, "bot.menu_teacher", name=name, classes=classes, tests=tests), [
        [btn(t(lang, "btn.new_test"), "nt")], [btn(t(lang, "btn.tests"), "tl"), btn(t(lang, "btn.classes"), "cl")], [app(t(lang, "btn.app"))],
        [btn(t(lang, "btn.help"), "h"), btn(t(lang, "btn.lang"), "lang")]]


def menu_student(lang: str, name: str, fresh: int) -> tuple:
    line = t(lang, "bot.student_new", n=fresh) if fresh else t(lang, "bot.student_none")
    return t(lang, "bot.menu_student", name=name, line=line), [
        [btn(t(lang, "btn.tests"), "st")], [btn(t(lang, "btn.code"), "code")], [btn(t(lang, "btn.help"), "h"), btn(t(lang, "btn.lang"), "lang")]]


def joined_student(lang: str) -> tuple:
    return t(lang, "bot.student_join"), [[btn(t(lang, "btn.code"), "code")], [btn(t(lang, "btn.menu"), "m")]]


def help_screen(lang: str, role: str | None) -> tuple:
    return t(lang, "bot.help_student" if role == "student" else "bot.help_teacher"), [back(lang)]


def new_test(lang: str) -> tuple:
    return t(lang, "bot.new_test"), [back(lang)]


def got_source(lang: str, src: dict) -> tuple:
    counts = [btn(t(lang, "btn.n", n=n), f"n:{src['id']}:{n}") for n in (5, 10, 15, 20)]
    return t(lang, "bot.got_source", title=src["title"], passages=src["passages"], chars=num(src["chars"])), [counts, back(lang)]


def ask_mix(lang: str, src: dict, n: int) -> tuple:
    mixes = [btn(t(lang, f"btn.mix_{m}"), f"x:{src['id']}:{n}:{m}") for m in ("easy", "mixed", "hard")]
    return t(lang, "bot.ask_mix", title=src["title"], n=n), [mixes, back(lang, f"n:{src['id']}")]


def draft_ready(lang: str, d: dict, has_app: bool) -> tuple:
    n = len(d["questions"])
    fewer = t(lang, "bot.fewer", asked=d["asked"]) if n < d["asked"] else ""
    rows = [[app(t(lang, "btn.review"), f"?t={d['id']}")]] if has_app else []
    rows += [[btn(t(lang, "btn.tests"), "+tl"), btn(t(lang, "btn.menu"), "+m")]]
    text = t(lang, "bot.draft_ready", title=d["title"], count=questions(lang, n), fewer=fewer)
    return (text if has_app else f"{text}\n\n{t(lang, 'bot.no_app')}"), rows


def tests_list(lang: str, items: list[dict]) -> tuple:
    if not items:
        return t(lang, "bot.tests_none"), [back(lang)]
    rows = []
    for it in items[:10]:
        key = "bot.test_draft_row" if it["status"] == "draft" else "bot.test_retest_row" if it["parent"] else "bot.test_row"
        rows.append([btn(t(lang, key, title=short(it["title"], 34), done=it["done"], people=it["people"]), f"t:{it['id']}")])
    return t(lang, "bot.tests"), [*rows, back(lang)]


def test_card(lang: str, d: dict, res: dict | None, an: dict | None, now: int) -> tuple:
    """A draft (review it in the app) or a published test: code, how many finished, the average, flags, the retest."""
    if d["status"] == "draft":
        return t(lang, "bot.card_draft", title=d["title"], count=questions(lang, len(d["questions"]))), [
            [app(t(lang, "btn.review"), f"?t={d['id']}")], back(lang, "tl")]
    st = res["stats"]
    flags = ""
    if an and an["n"] >= A.MIN_FLAGS:
        keys = sum(1 for r in an["questions"] if r["flag"] == "key")
        hard = sum(1 for r in an["questions"] if r["flag"] == "hard")
        flags = (t(lang, "bot.flags", n=keys) if keys else "") + (t(lang, "bot.flags_hard", n=hard) if hard else "")
    code = t(lang, "bot.card_retest") if d["parent"] else t(lang, "bot.card_code", code=d["code"])
    deadline = t(lang, "bot.card_deadline", when=when(lang, d["deadline"], now)) if d["deadline"] else ""
    cls = next((k["name"] for k in d["classes"] if k["id"] == d["grp"]), "")
    text = t(lang, "bot.card", title=d["title"], cls=cls, count=questions(lang, len(d["questions"])), minutes=minutes(lang, d["minutes"]),
             deadline=deadline, code=Raw(code), done_lbl=t(lang, "lbl.done"), done=st["done"], people=st["people"], avg_lbl=t(lang, "lbl.avg"),
             avg=pct(lang, st["avg"]) if st["done"] else "—", flags=Raw(flags))
    rows = [[app(t(lang, "btn.results"), f"?r={d['id']}"), app(t(lang, "btn.analysis"), f"?a={d['id']}")]]
    if an and not d["parent"] and an["retest"] is None and an["plan"]["topics"] and an["plan"]["count"]:
        rows.append([btn(t(lang, "btn.retest"), f"rq:{d['id']}")])
    if st["done"]:
        rows.append([btn(t(lang, "btn.csv"), f"csv:{d['id']}")])
    return text, [*rows, back(lang, "tl")]


def retest_ask(lang: str, tid: int, plan: dict) -> tuple:
    names = ", ".join(n.split(" ")[0] for n in plan["names"][:12]) + ("…" if len(plan["names"]) > 12 else "")
    return t(lang, "bot.retest_ask", topics=", ".join(plan["topics"]), count=plan["count"], names=names), [
        [btn(t(lang, "btn.retest_send"), f"rx:{tid}")], back(lang, f"t:{tid}")]


def retest_sent(lang: str, tid: int, info: dict) -> tuple:
    text = t(lang, "bot.retest_again") if info.get("again") else t(lang, "bot.retest_sent", students=info["students"], count=questions(lang, info["count"]))
    return text, [[app(t(lang, "btn.results"), f"?r={info['id']}")], back(lang, f"t:{tid}")]


def classes_list(lang: str, items: list[dict]) -> tuple:
    rows = [[btn(t(lang, "bot.class_row", name=k["name"], n=students(lang, k["students"])), f"c:{k['id']}")] for k in items[:20]]
    return t(lang, "bot.classes"), [*rows, [btn(t(lang, "btn.new_class"), "cn")], back(lang)]


def class_screen(lang: str, k: dict, link: str, days: int) -> tuple:
    names = ", ".join(s["name"].split(" ")[0] for s in k["students"][:40])
    return t(lang, "bot.class", name=k["name"], count=students(lang, len(k["students"])), names=names, days=days, link=link), [back(lang, "cl")]


def ask_class(lang: str) -> tuple:
    return t(lang, "bot.ask_class"), [back(lang, "cl")]


def ask_code(lang: str) -> tuple:
    return t(lang, "bot.ask_code"), [back(lang)]


def my_tests(lang: str, items: list[dict]) -> tuple:
    if not items:
        return t(lang, "bot.my_none"), [back(lang)]
    rows = []
    for it in items[:10]:
        title = short(it["title"], 32)
        key = {"new": "bot.my_new", "working": "bot.my_working", "done": "bot.my_done", "closed": "bot.my_closed"}[it["status"]]
        rows.append([app(t(lang, key, title=title, count=questions(lang, it["count"]) if it["status"] == "new" else it["count"], score=it.get("score", 0)),
                         f"?s={it['id']}")])
    return t(lang, "bot.my_tests"), [*rows, back(lang)]


def code_joined(lang: str, j: dict) -> tuple:
    return t(lang, "bot.joined_code", cls=j["class"], title=j["title"]), [[app(t(lang, "btn.start_test"), f"?s={j['test']}")], [btn(t(lang, "btn.menu"), "+m")]]


def note(lang: str, n: dict, now: int) -> tuple:
    """A message the bot sends on its own (from the service's notes)."""
    deadline = t(lang, "note.deadline", when=when(lang, n["deadline"], now)) if n.get("deadline") else ""
    k = n["kind"]
    if k == "new_test":
        return t(lang, "note.new_test", title=n["title"], count=questions(lang, n["count"]), minutes=minutes(lang, n["minutes"]), deadline=Raw(deadline)), [
            [app(t(lang, "btn.start_test"), f"?s={n['test']}")]]
    if k == "retest":
        return t(lang, "note.retest", title=n["title"], topics=", ".join(n["topics"]), count=questions(lang, n["count"]), minutes=minutes(lang, n["minutes"]),
                 deadline=Raw(deadline)), [[app(t(lang, "btn.start_test"), f"?s={n['test']}")]]
    if k == "reminder":
        return t(lang, "note.reminder", title=n["title"], when=when(lang, n["deadline"], now)), [[app(t(lang, "btn.start_test"), f"?s={n['test']}")]]
    head = t(lang, "note.summary_all" if n["reason"] == "all" else "note.summary_deadline", title=n["title"])
    flags = (t(lang, "bot.flags", n=n["flags"]["key"]) if n["flags"]["key"] else "") + (t(lang, "bot.flags_hard", n=n["flags"]["hard"]) if n["flags"]["hard"] else "")
    prog = n.get("progress")
    progress = t(lang, "note.progress", before=pct(lang, prog["before"]), after=pct(lang, prog["after"])) if prog and prog["retook"] else ""
    text = t(lang, "note.summary", head=Raw(head), done_lbl=t(lang, "lbl.done"), done=n["done"], people=n["people"], avg_lbl=t(lang, "lbl.avg"),
             avg=pct(lang, n["avg"]), median_lbl=t(lang, "lbl.median"), median=pct(lang, n["median"]), flags=Raw(flags), progress=Raw(progress))
    return text, [[app(t(lang, "btn.results"), f"?r={n['test']}"), app(t(lang, "btn.analysis"), f"?a={n['test']}")]]
