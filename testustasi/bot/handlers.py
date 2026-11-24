"""The bot: buttons, texts and files. ``/start`` (with an invite ``g<class>_<expiry>_<sig>`` or a test code ``t<CODE>``) is
the only command. A teacher's long text or file becomes a source, then a draft; a student's 6-character message is a
test code. Every button's data is checked against a fixed pattern; roles and ownership are checked by the service."""

from __future__ import annotations

import re

from aiogram import F, Router
from aiogram.filters import CommandObject, CommandStart
from aiogram.types import BufferedInputFile, CallbackQuery, Message

from ..common import Refused
from ..core.clock import civil, hhmm, local_day, local_minute
from ..groups import norm_code
from ..i18n import t
from ..sources import SourceError, extract_async
from . import views
from .setup import show

router = Router()
fallback = Router()
N = r"(\d{1,12})"
PATTERNS = [(name, re.compile(rx)) for name, rx in (
    ("menu", r"m"), ("lang", r"lang"), ("help", r"h"), ("teacher", r"role:t"), ("student", r"role:s"), ("new", r"nt"), ("count", rf"n:{N}"),
    ("mix", rf"n:{N}:(5|10|15|20)"), ("make", rf"x:{N}:(5|10|15|20):(easy|mixed|hard)"), ("tests", r"tl"), ("test", rf"t:{N}"), ("retest_ask", rf"rq:{N}"),
    ("retest", rf"rx:{N}"), ("csv", rf"csv:{N}"), ("classes", r"cl"), ("class", rf"c:{N}"), ("new_class", r"cn"), ("mine", r"st"), ("code", r"code"))]
CSV_LABELS = ("no", "name", "score", "pct", "grade", "time", "status", "at")


async def menu_screen(svc, me: int, lang: str) -> tuple:
    u = await svc.user(me)
    if u["role"] == "teacher":
        return views.menu_teacher(lang, u["name"], len(await svc.classes(me)), len(await svc.tests(me)))
    if u["role"] == "student":
        return views.menu_student(lang, u["name"], sum(1 for x in await svc.my_tests(me) if x["status"] == "new"))
    return views.hello(lang)


def csv_labels(lang: str) -> dict[str, str]:
    out = {k: t(lang, f"csv.{k}") for k in CSV_LABELS}
    out.update({f"st_{s}": t(lang, f"csv.st_{s}") for s in ("done", "working", "waiting")})
    return out


def stamp(ms: int) -> str:
    y, m, d = civil(local_day(ms))
    return f"{d:02d}.{m:02d}.{y} {hhmm(local_minute(ms))}"


async def joined(message: Message, me: int, lang: str, svc, cfg, payload: str) -> None:
    if payload.startswith("g"):
        k = await svc.join_invite(me, payload)
        text, rows = await menu_screen(svc, me, lang)
        await show(message, (t(lang, "bot.joined", cls=k["name"], teacher=k["teacher"]) + "\n\n" + text, rows), cfg)
    else:
        await show(message, views.code_joined(lang, await svc.join_code(me, payload[1:])), cfg)


@router.message(CommandStart())
async def start(message: Message, command: CommandObject, me: int, lang: str, svc, cfg, codes) -> None:
    await svc.set_pending(me, None)
    arg = (command.args or "").strip()[:64]
    if arg[:1] in ("g", "t") and len(arg) > 1:
        if arg[0] == "t" and not codes.allow(me):
            raise Refused("rate")
        await joined(message, me, lang, svc, cfg, arg)
        return
    await show(message, await menu_screen(svc, me, lang), cfg)


async def source_screen(message: Message, me: int, lang: str, svc, cfg, text: str, title: str = "", kind: str = "text") -> None:
    src = await svc.add_source(me, text, title, kind)
    await show(message, views.got_source(lang, src), cfg)


@router.message(F.document)
async def document(message: Message, me: int, lang: str, role, svc, cfg) -> None:
    if role != "teacher":
        await message.answer(t(lang, "bot.file_student"))
        return
    doc = message.document
    if (doc.file_size or 0) > cfg.file_max_bytes:
        raise Refused("too_big")
    wait = await message.answer(t(lang, "bot.reading"))
    try:
        data = await message.bot.download(doc.file_id)
        raw = data.read(cfg.file_max_bytes + 1) if data else b""
        text, kind = await extract_async(raw, cfg.file_max_bytes, cfg.pdf_max_pages)
    except SourceError as err:
        raise Refused(err.code) from err
    finally:
        await message.bot.delete_message(message.chat.id, wait.message_id)
    name = re.sub(r"\.(pdf|docx|txt)$", "", doc.file_name or "", flags=re.I).replace("_", " ")[:80]
    await source_screen(message, me, lang, svc, cfg, text, name, kind)


@router.message(F.text)
async def typed(message: Message, me: int, lang: str, role, svc, cfg, codes) -> None:
    text = message.text or ""
    pend = await svc.pending(me)
    if pend and pend.get("kind") == "class_name":
        await svc.set_pending(me, None)
        k = await svc.create_class(me, text[:40])
        screen = views.classes_list(lang, await svc.classes(me))
        await show(message, (t(lang, "bot.class_made", name=k["name"]) + "\n\n" + screen[0], screen[1]), cfg)
        return
    if role != "teacher" and (norm_code(text) or (pend and pend.get("kind") == "code")):
        await svc.set_pending(me, None)
        if not codes.allow(me):
            raise Refused("rate")
        await show(message, views.code_joined(lang, await svc.join_code(me, text)), cfg)
        return
    if role == "teacher":
        if len(text.strip()) < 150:
            screen = await menu_screen(svc, me, lang)
            await show(message, (t(lang, "bot.short_text") + "\n\n" + screen[0], screen[1]), cfg)
            return
        await source_screen(message, me, lang, svc, cfg, text)
        return
    await show(message, await menu_screen(svc, me, lang), cfg)


async def route(data: str, me: int, lang: str, svc, cfg, cb: CallbackQuery, notifier) -> tuple | None:
    found = next(((n, m) for n, rx in PATTERNS if (m := rx.fullmatch(data))), None)
    if found is None:
        await cb.answer(t(lang, "bot.stale"), show_alert=True)
        return await menu_screen(svc, me, lang)
    kind, m = found
    g = [int(x) if x.isdigit() else x for x in m.groups()]
    has_app = bool(cfg.webapp_url)
    if kind == "menu":
        await svc.set_pending(me, None)
        return await menu_screen(svc, me, lang)
    if kind == "lang":
        lang = await svc.set_lang(me, "ru" if lang == "uz" else "uz")
        return await menu_screen(svc, me, lang)
    if kind == "help":
        return views.help_screen(lang, (await svc.user(me))["role"])
    if kind == "teacher":
        await svc.set_role(me, "teacher")
        return await menu_screen(svc, me, lang)
    if kind == "student":
        await svc.set_role(me, "student")
        return views.joined_student(lang)
    if kind == "code":
        await svc.set_pending(me, {"kind": "code"})
        return views.ask_code(lang)
    if kind == "mine":
        return views.my_tests(lang, await svc.my_tests(me))
    await svc.need_teacher(me)
    if kind == "new":
        return views.new_test(lang)
    if kind in ("count", "mix"):
        src = await svc.own_source(me, g[0])
        src = {**src, "passages": 0, "chars": len(src["body"])}
        return views.got_source(lang, {**src, "passages": len(__import__("testustasi.core.passages", fromlist=["split"]).split(src["body"]))}) \
            if kind == "count" else views.ask_mix(lang, src, g[1])
    if kind == "make":
        await show(cb, (t(lang, "bot.making"), []), cfg)
        return views.draft_ready(lang, await svc.make_draft(me, g[0], g[1], g[2]), has_app)
    if kind == "tests":
        return views.tests_list(lang, await svc.tests(me))
    if kind == "test":
        d = await svc.draft_view(me, g[0])
        res = await svc.results(me, g[0]) if d["status"] == "published" else None
        an = await svc.analysis(me, g[0]) if res else None
        return views.test_card(lang, d, res, an, svc.now())
    if kind == "retest_ask":
        return views.retest_ask(lang, g[0], (await svc.analysis(me, g[0]))["plan"])
    if kind == "retest":
        info, notes = await svc.retest(me, g[0])
        await notifier.send(notes)
        return views.retest_sent(lang, g[0], info)
    if kind == "csv":
        title, text = await svc.csv(me, g[0], csv_labels(lang), stamp)
        name = re.sub(r"[^\w\- ]+", "", title)[:40].strip() or "natijalar"
        await cb.answer()
        await cb.bot.send_document(me, BufferedInputFile(text.encode("utf-8"), f"{name}.csv"), caption=t(lang, "bot.csv", title=title))
        return None
    if kind == "classes":
        return views.classes_list(lang, await svc.classes(me))
    if kind == "class":
        k = await svc.class_detail(me, g[0])
        return views.class_screen(lang, k, f"https://t.me/{cfg.bot_username}?start={await svc.invite(me, g[0])}", cfg.invite_days)
    await svc.set_pending(me, {"kind": "class_name"})
    return views.ask_class(lang)


@router.callback_query()
async def button(cb: CallbackQuery, me: int, lang: str, svc, notifier, cfg) -> None:
    data = (cb.data or "")[:64]
    keep = data.startswith("+")  # a button under a message that stays in the chat: answer with a new message
    screen = await route(data[1:] if keep else data, me, lang, svc, cfg, cb, notifier)
    if screen is not None:
        await show(cb, screen, cfg, new=keep)


@fallback.message()
async def other(message: Message, me: int, lang: str, svc, cfg) -> None:
    await show(message, await menu_screen(svc, me, lang), cfg)
