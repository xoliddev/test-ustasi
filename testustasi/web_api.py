"""The Mini App's JSON API, always as the signed-in Telegram user. A teacher's routes reach only that teacher's
classes and tests; a student's only the tests given to them, and the solving routes never return a correct answer,
an explanation or a quote before the attempt is submitted (and, with attempts left, not even then)."""

from __future__ import annotations

from collections.abc import Awaitable, Callable

from aiohttp import web

from .common import Refused
from .i18n import csv_labels, stamp
from .service import Service
from .web import MAX_TEXT_BODY, body

ID = r"{id:\d{1,12}}"
QID = r"{qid:\d{1,12}}"


def add_routes(r: web.UrlDispatcher, svc: Service, ME: web.RequestKey, notify: Callable[[list[dict]], Awaitable[None]], bot_username: str,
               invite_days: int) -> None:
    def j(data: object) -> web.Response:
        return web.json_response(data)

    def num(request: web.Request, key: str = "id") -> int:
        return int(request.match_info[key])

    async def role(request: web.Request) -> str | None:
        return (await svc.user(request[ME]))["role"]

    async def me(request: web.Request) -> web.Response:
        return j(await svc.me(request[ME]))

    async def lang(request: web.Request) -> web.Response:
        return j({"lang": await svc.set_lang(request[ME], (await body(request)).get("lang"))})

    async def tests(request: web.Request) -> web.Response:
        if await role(request) == "teacher":
            return j({"items": await svc.tests(request[ME])})
        return j({"items": await svc.my_tests(request[ME])})

    async def draft(request: web.Request) -> web.Response:
        data = await body(request, MAX_TEXT_BODY)
        src = await svc.add_source(request[ME], data.get("text"), data.get("title") or "")
        return j(await svc.make_draft(request[ME], src["id"], data.get("n"), data.get("mix")))

    async def test(request: web.Request) -> web.Response:
        if await role(request) == "teacher":
            return j(await svc.draft_view(request[ME], num(request)))
        return j(await svc.test_card(request[ME], num(request)))

    async def settings(request: web.Request) -> web.Response:
        return j(await svc.set_settings(request[ME], num(request), await body(request)))

    async def publish(request: web.Request) -> web.Response:
        view, notes = await svc.publish(request[ME], num(request))
        await notify(notes)
        return j(view)

    async def edit(request: web.Request) -> web.Response:
        return j(await svc.edit_question(request[ME], num(request), num(request, "qid"), await body(request)))

    async def delete(request: web.Request) -> web.Response:
        return j(await svc.delete_question(request[ME], num(request), num(request, "qid")))

    async def regen(request: web.Request) -> web.Response:
        return j(await svc.regen_question(request[ME], num(request), num(request, "qid")))

    async def move(request: web.Request) -> web.Response:
        return j(await svc.move_question(request[ME], num(request), num(request, "qid"), (await body(request)).get("step")))

    async def results(request: web.Request) -> web.Response:
        return j(await svc.results(request[ME], num(request)))

    async def analysis(request: web.Request) -> web.Response:
        return j(await svc.analysis(request[ME], num(request)))

    async def csv(request: web.Request) -> web.Response:
        lang = (await svc.user(request[ME]))["lang"]
        title, text = await svc.csv(request[ME], num(request), csv_labels(lang), stamp)
        return j({"name": f"{title}.csv", "csv": text})

    async def retest(request: web.Request) -> web.Response:
        info, notes = await svc.retest(request[ME], num(request))
        await notify(notes)
        return j(info)

    async def classes(request: web.Request) -> web.Response:
        return j({"items": await svc.classes(request[ME])})

    async def class_add(request: web.Request) -> web.Response:
        return j(await svc.create_class(request[ME], (await body(request)).get("name")))

    async def class_one(request: web.Request) -> web.Response:
        return j(await svc.class_detail(request[ME], num(request)))

    async def invite(request: web.Request) -> web.Response:
        payload = await svc.invite(request[ME], num(request))
        return j({"link": f"https://t.me/{bot_username}?start={payload}", "days": invite_days})

    async def start(request: web.Request) -> web.Response:
        view, notes = await svc.start(request[ME], num(request))
        await notify(notes)
        return j(view)

    async def attempt(request: web.Request) -> web.Response:
        return j(await svc.attempt_view(request[ME], num(request)))

    async def answer(request: web.Request) -> web.Response:
        data = await body(request)
        res, notes = await svc.answer(request[ME], num(request), data.get("pos"), data.get("choice"))
        await notify(notes)
        return j(res)

    async def submit(request: web.Request) -> web.Response:
        res, notes = await svc.submit(request[ME], num(request))
        await notify(notes)
        return j(res)

    async def result(request: web.Request) -> web.Response:
        if await role(request) != "student":
            raise Refused("forbidden")
        return j(await svc.result(request[ME], num(request)))

    r.add_get("/api/me", me)
    r.add_post("/api/lang", lang)
    r.add_get("/api/tests", tests)
    r.add_post("/api/drafts", draft)
    r.add_get(f"/api/tests/{ID}", test)
    r.add_post(f"/api/tests/{ID}/settings", settings)
    r.add_post(f"/api/tests/{ID}/publish", publish)
    r.add_post(f"/api/tests/{ID}/questions/{QID}", edit)
    r.add_post(f"/api/tests/{ID}/questions/{QID}/delete", delete)
    r.add_post(f"/api/tests/{ID}/questions/{QID}/regen", regen)
    r.add_post(f"/api/tests/{ID}/questions/{QID}/move", move)
    r.add_get(f"/api/tests/{ID}/results", results)
    r.add_get(f"/api/tests/{ID}/analysis", analysis)
    r.add_get(f"/api/tests/{ID}/csv", csv)
    r.add_post(f"/api/tests/{ID}/retest", retest)
    r.add_get("/api/classes", classes)
    r.add_post("/api/classes", class_add)
    r.add_get(f"/api/classes/{ID}", class_one)
    r.add_post(f"/api/classes/{ID}/invite", invite)
    r.add_post(f"/api/tests/{ID}/start", start)
    r.add_get(f"/api/tests/{ID}/result", result)
    r.add_get(f"/api/attempts/{ID}", attempt)
    r.add_post(f"/api/attempts/{ID}/answer", answer)
    r.add_post(f"/api/attempts/{ID}/submit", submit)
