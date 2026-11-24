"""HTTP: initData HMAC + freshness, teacher-only routes, students' payloads without answers before submitting (checked
on the real API responses), teachers kept apart, strict input, body caps, CSP, and every real page address opens (a
folder served by add_static would answer 403)."""

from __future__ import annotations

import json
from contextlib import asynccontextmanager

from aiohttp.test_utils import TestClient, TestServer

from testustasi.security import sign_init_data
from testustasi.web import make_app

from .helpers import FOTO, JASUR, MADINA, NODIRA, OTHER_TEACHER, STRANGER, published, service_env

TOKEN = "123456:TEST-ONLY-NOT-A-REAL-TOKEN"


class Spy:
    def __init__(self) -> None:
        self.notes: list[dict] = []

    async def send(self, notes):
        self.notes.extend(notes)


def init_data(uid: int, clock, age: int = 0, token: str = TOKEN) -> str:
    fields = {"auth_date": str(clock() // 1000 - age), "query_id": "AAE-test", "user": json.dumps({"id": uid, "first_name": f"U{uid}", "language_code": "uz"})}
    return sign_init_data(fields, token)


@asynccontextmanager
async def client(rate: int = 1000):
    async with service_env() as (svc, clock):
        spy = Spy()
        app = make_app(svc, TOKEN, spy, rate_per_minute=rate, bot_username="ustasi_test_bot")
        async with TestClient(TestServer(app)) as c:
            def h(uid, **kw):
                return {"Authorization": f"tma {init_data(uid, clock, **kw)}"}
            yield c, svc, clock, spy, h


async def test_every_page_address_opens():
    async with client() as (c, *_):
        for path in ("/webapp/", "/webapp/main.js", "/webapp/ui.js", "/webapp/s-solve.js", "/webapp/t-analysis.js", "/webapp/app.css",
                     "/shared/locales/uz.json", "/shared/generate.js", "/shared/analysis.js", "/healthz"):
            r = await c.get(path)
            assert r.status == 200, path
        page = await c.get("/webapp/?s=5")
        assert "text/html" in page.headers["Content-Type"] and "Test Ustasi" in await page.text()
        assert "default-src 'self'" in page.headers["Content-Security-Policy"] and page.headers["X-Content-Type-Options"] == "nosniff"
        for path in ("/", "/webapp"):
            r = await c.get(path, allow_redirects=False)
            assert r.status == 302 and r.headers["Location"] == "/webapp/"
        assert (await c.get("/api/nope")).status == 401, "unknown private routes still need initData"
        for bad in ("/webapp/../testustasi/config.py", "/shared/../.env", "/nope", "/demo/index.html"):
            assert (await c.get(bad)).status == 404, bad


async def test_init_data_is_checked():
    async with client() as (c, _svc, clock, _spy, h):
        assert (await c.get("/api/me")).status == 401
        assert (await c.get("/api/me", headers=h(JASUR, age=7200))).status == 401, "stale"
        assert (await c.get("/api/me", headers={"Authorization": f"tma {init_data(JASUR, clock, token='999:OTHER')}"})).status == 401
        forged = init_data(JASUR, clock).replace(f"%22id%22%3A+{JASUR}", f"%22id%22%3A+{NODIRA}")
        assert (await c.get("/api/me", headers={"Authorization": f"tma {forged}"})).status == 401
        assert (await (await c.get("/api/me", headers=h(JASUR))).json())["role"] == "student"


async def test_students_get_no_answers_before_submitting():
    async with client() as (c, svc, clock, _spy, h):
        t = await published(svc, clock)
        card = await (await c.get(f"/api/tests/{t['id']}", headers=h(JASUR))).json()
        assert set(card) >= {"title", "count", "minutes", "left"} and "questions" not in card
        start = await c.post(f"/api/tests/{t['id']}/start", json={}, headers=h(JASUR))
        view = await start.json()
        blob = json.dumps(view, ensure_ascii=False)
        for word in ("correct", "explanation", "quote", "qid", "uid"):
            assert f'"{word}"' not in blob, word
        assert all(q["quote"] not in blob and q["explanation"] not in blob for q in t["questions"] if q["explanation"])
        assert (await c.get(f"/api/tests/{t['id']}/result", headers=h(JASUR))).status == 400, "not submitted yet"
        for path in (f"/api/tests/{t['id']}/results", f"/api/tests/{t['id']}/analysis", f"/api/tests/{t['id']}/csv", "/api/classes"):
            assert (await c.get(path, headers=h(JASUR))).status == 403, path
        assert (await c.post(f"/api/tests/{t['id']}/retest", json={}, headers=h(JASUR))).status == 403
        assert (await c.get(f"/api/attempts/{view['attempt']}", headers=h(MADINA))).status in (401, 404)
        assert (await c.get(f"/api/attempts/{view['attempt']}", headers=h(STRANGER))).status == 404
        ans = await c.post(f"/api/attempts/{view['attempt']}/answer", json={"pos": 0, "choice": 2}, headers=h(JASUR))
        assert (await ans.json())["answered"] == 1
        for bad in ({"pos": "0", "choice": 1}, {"pos": 0, "choice": 7}, {"pos": 99, "choice": 1}, {"pos": True, "choice": 1}):
            assert (await c.post(f"/api/attempts/{view['attempt']}/answer", json=bad, headers=h(JASUR))).status == 400, bad
        res = await (await c.post(f"/api/attempts/{view['attempt']}/submit", json={}, headers=h(JASUR))).json()
        assert res["total"] == 10 and res["reveal"] and res["mistakes"]
        again = await (await c.post(f"/api/attempts/{view['attempt']}/submit", json={}, headers=h(JASUR))).json()
        assert again["score"] == res["score"], "a second submit changes nothing"


async def test_teacher_routes_and_teachers_apart():
    async with client() as (c, svc, _clock, spy, h):
        r = await c.post("/api/drafts", json={"text": FOTO, "title": "Fotosintez", "n": 10, "mix": "mixed"}, headers=h(NODIRA))
        d = await r.json()
        assert r.status == 200 and len(d["questions"]) == 10 and all(q["quote"] for q in d["questions"])
        q = d["questions"][0]
        assert (await c.post(f"/api/tests/{d['id']}/questions/{q['id']}", json={"options": ["A", "A", "B", "C"]}, headers=h(NODIRA))).status == 400
        assert (await c.post(f"/api/tests/{d['id']}/questions/{q['id']}/move", json={"step": 1}, headers=h(NODIRA))).status == 200
        assert (await c.post(f"/api/tests/{d['id']}/settings", json={"grp": 1, "minutes": 15}, headers=h(NODIRA))).status == 200
        await svc.create_class(OTHER_TEACHER, "9-A")
        for method, path in (("get", f"/api/tests/{d['id']}"), ("post", f"/api/tests/{d['id']}/publish"), ("post", f"/api/tests/{d['id']}/questions/{q['id']}/delete"),
                             ("get", "/api/classes/1"), ("post", "/api/classes/1/invite")):
            resp = await getattr(c, method)(path, headers=h(OTHER_TEACHER), **({"json": {}} if method == "post" else {}))
            assert resp.status == 404, path
        pub = await c.post(f"/api/tests/{d['id']}/publish", json={}, headers=h(NODIRA))
        assert pub.status == 200 and len(spy.notes) == 25
        inv = await (await c.post("/api/classes/1/invite", json={}, headers=h(NODIRA))).json()
        assert inv["link"].startswith("https://t.me/ustasi_test_bot?start=g1_") and inv["days"] == 14
        res = await (await c.get(f"/api/tests/{d['id']}/results", headers=h(NODIRA))).json()
        assert res["stats"]["people"] == 25 and res["stats"]["done"] == 0
        csv = await (await c.get(f"/api/tests/{d['id']}/csv", headers=h(NODIRA))).json()
        assert csv["name"] == "Fotosintez.csv" and csv["csv"].startswith("﻿№;Ism;Ball")
        items = (await (await c.get("/api/tests", headers=h(OTHER_TEACHER))).json())["items"]
        assert items == []


async def test_inputs_are_strict_and_bodies_capped():
    async with client() as (c, _svc, _clock, _spy, h):
        assert (await c.post("/api/drafts", data=b"{" * 20, headers=h(NODIRA))).status == 400
        assert (await c.post("/api/drafts", json={"text": "x" * 200_000, "n": 10, "mix": "mixed"}, headers=h(NODIRA))).status == 413
        assert (await c.post("/api/lang", data=b"x" * 20_000, headers=h(NODIRA))).status == 413
        assert (await c.post("/api/drafts", json={"text": FOTO, "n": 7, "mix": "mixed"}, headers=h(NODIRA))).status == 400
        assert (await c.post("/api/drafts", json={"text": FOTO, "n": 10, "mix": "x"}, headers=h(NODIRA))).status == 400
        assert (await c.post("/api/lang", json={f"k{i}": i for i in range(9)}, headers=h(NODIRA))).status == 400
        assert (await c.get("/api/tests/abc", headers=h(NODIRA))).status == 401 or (await c.get("/api/tests/abc", headers=h(NODIRA))).status == 404
        r = await c.get("/api/me", headers=h(NODIRA))
        assert r.headers["Cache-Control"] == "no-store"


async def test_rate_limit_per_user():
    async with client(rate=10) as (c, _svc, _clock, _spy, h):
        codes = [(await c.get("/api/me", headers=h(JASUR))).status for _ in range(14)]
        assert codes[:10] == [200] * 10 and 429 in codes[10:]
        assert (await c.get("/api/me", headers=h(NODIRA))).status == 200, "per user, not global"
