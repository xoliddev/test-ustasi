"""The service's foundation: the clock, people and their one role, and the scoped lookups every rule uses.

A person is either a teacher (owns classes, sources and tests) or a student (belongs to classes, solves tests) —
never both. Every lookup of a teacher's data takes the teacher's id and every student lookup checks that the test was
given to that student; a row of somebody else's is "not found", so ids reveal nothing."""

from __future__ import annotations

import json
import time
from collections.abc import Callable
from pathlib import Path

from .common import Refused
from .core.clock import local_day
from .core.text import InputError, clean
from .db import Database

DATA = Path(__file__).resolve().parent.parent / "shared" / "data"
PEND_MINUTES = 30


def load(name: str):
    with open(DATA / f"{name}.json", encoding="utf-8") as fh:
        return json.load(fh)


def checked(fn, *args):
    """Run a core validator; its InputError becomes a Refused with the same code."""
    try:
        return fn(*args)
    except InputError as err:
        raise Refused(err.code) from err


def is_id(value: object, top: int = 10**12) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and -top < value < top and value != 0


def qrow(r: dict) -> dict:
    return {**r, "options": json.loads(r["options"])}


class Base:
    def __init__(self, db: Database, clock: Callable[[], int] | None = None, invite_secret: bytes = b"dev-only", invite_days: int = 14,
                 ai=None, ai_per_day: int = 20, remind_hours: int = 2) -> None:
        self.db = db
        self.clock = clock or (lambda: int(time.time() * 1000))
        self.invite_secret = invite_secret
        self.invite_days = invite_days
        self.ai = ai
        self.ai_per_day = ai_per_day
        self.remind_hours = remind_hours
        self.texts = {t["id"]: t for t in load("texts")}

    def now(self) -> int:
        return self.clock()

    def today(self) -> int:
        return local_day(self.now())

    # ── people ──
    async def touch_user(self, uid: int, name: str, lang_code: str | None) -> dict:
        row = await self.user(uid)
        if row is None:
            lang = "ru" if (lang_code or "")[:2].lower() == "ru" else "uz"
            async with self.db.tx() as c:
                await c.execute("INSERT OR IGNORE INTO users (id, name, lang, created_at) VALUES (?, ?, ?, ?)",
                                (uid, clean(name, 64) or "Foydalanuvchi", lang, self.now()))
            row = await self.user(uid)
        return row

    async def user(self, uid: int) -> dict | None:
        return await self.db.one("SELECT * FROM users WHERE id = ?", (uid,))

    async def set_lang(self, uid: int, lang: object) -> str:
        if lang not in ("uz", "ru"):
            raise Refused("generic")
        async with self.db.tx() as c:
            await c.execute("UPDATE users SET lang = ? WHERE id = ?", (lang, uid))
        return lang

    async def set_pending(self, uid: int, pend: dict | None) -> None:
        """What the bot waits for from this person next (a class name, a test code, the count of questions)."""
        async with self.db.tx() as c:
            await c.execute("UPDATE users SET pend = ? WHERE id = ?", (json.dumps({**pend, "at": self.now()}) if pend else None, uid))

    async def pending(self, uid: int) -> dict | None:
        u = await self.user(uid)
        if not u or not u["pend"]:
            return None
        pend = json.loads(u["pend"])
        return pend if self.now() - pend.get("at", 0) < PEND_MINUTES * 60_000 else None

    # ── roles ──
    async def set_role(self, uid: int, role: str, c=None) -> str:
        """The first role sticks: a teacher never becomes a student and the other way round."""
        u = await (self.q1(c, "SELECT role FROM users WHERE id = ?", (uid,)) if c is not None else self.db.one("SELECT role FROM users WHERE id = ?", (uid,)))
        if u is None:
            raise Refused("auth")
        if u["role"] == role:
            return role
        if u["role"] is not None:
            raise Refused(f"role_{u['role']}")
        if c is not None:
            await c.execute("UPDATE users SET role = ? WHERE id = ? AND role IS NULL", (role, uid))
        else:
            async with self.db.tx() as cc:
                await cc.execute("UPDATE users SET role = ? WHERE id = ? AND role IS NULL", (role, uid))
        return role

    async def need_teacher(self, uid: int, c=None) -> dict:
        u = await (self.q1(c, "SELECT * FROM users WHERE id = ?", (uid,)) if c is not None else self.user(uid))
        if u is None or u["role"] != "teacher":
            raise Refused("forbidden")
        return u

    async def me(self, uid: int) -> dict:
        u = await self.user(uid)
        if u is None:
            raise Refused("auth")
        return {"id": uid, "name": u["name"], "lang": u["lang"], "role": u["role"], "now": self.now(), "today": self.today()}

    # ── scoped lookups ──
    async def teacher_test(self, uid: int, tid: object, c=None) -> dict:
        """A test of this teacher, or "not found" (never "forbidden": an id says nothing about another teacher)."""
        if not is_id(tid):
            raise Refused("generic")
        await self.need_teacher(uid, c)
        sql, args = "SELECT * FROM tests WHERE id = ? AND teacher = ?", (tid, uid)
        t = await (self.q1(c, sql, args) if c is not None else self.db.one(sql, args))
        if t is None:
            raise Refused("not_found")
        return t

    async def student_test(self, uid: int, tid: object, c=None) -> dict:
        """A published test given to this student (their class's test, or a retest sent to them), or "not found"."""
        if not is_id(tid):
            raise Refused("generic")
        sql = "SELECT t.* FROM tests t JOIN targets g ON g.test = t.id AND g.user = ? WHERE t.id = ? AND t.status = 'published'"
        t = await (self.q1(c, sql, (uid, tid)) if c is not None else self.db.one(sql, (uid, tid)))
        if t is None:
            raise Refused("not_found")
        return t

    async def questions_of(self, tid: int, c=None) -> list[dict]:
        sql = "SELECT * FROM questions WHERE test = ? ORDER BY pos, id"
        rows = await (self.qa(c, sql, (tid,)) if c is not None else self.db.all(sql, (tid,)))
        return [qrow(r) for r in rows]

    async def people_of(self, tid: int, c=None) -> list[dict]:
        sql = "SELECT u.id, u.name FROM targets g JOIN users u ON u.id = g.user WHERE g.test = ? ORDER BY u.name, u.id"
        return await (self.qa(c, sql, (tid,)) if c is not None else self.db.all(sql, (tid,)))

    async def attempts_of(self, tid: int, c=None) -> list[dict]:
        """Every attempt of a test with its answers ({question id: original option}) and how many are answered."""
        q = (lambda sql, a: self.qa(c, sql, a)) if c is not None else self.db.all
        rows = await q("SELECT * FROM attempts WHERE test = ? ORDER BY id", (tid,))
        ans = await q("SELECT a.attempt, a.question, a.choice FROM answers a JOIN attempts t ON t.id = a.attempt WHERE t.test = ?", (tid,))
        by: dict[int, dict[int, int]] = {}
        for a in ans:
            by.setdefault(a["attempt"], {})[a["question"]] = a["choice"]
        for r in rows:
            r["answers"] = by.get(r["id"], {})
            r["answered"] = len(r["answers"])
        return rows

    async def once(self, c, key: str) -> bool:
        """Mark ``key`` sent; False if it already was (a summary or a reminder goes out once)."""
        return await self.run(c, "INSERT OR IGNORE INTO sent (key, at) VALUES (?, ?)", (key, self.now())) == 1

    # ── shared queries ──
    @staticmethod
    async def q1(c, sql: str, args: tuple = ()) -> dict | None:
        async with c.execute(sql, args) as cur:
            row = await cur.fetchone()
        return dict(row) if row else None

    @staticmethod
    async def qa(c, sql: str, args: tuple = ()) -> list[dict]:
        async with c.execute(sql, args) as cur:
            return [dict(r) for r in await cur.fetchall()]

    @staticmethod
    async def run(c, sql: str, args: tuple = ()) -> int:
        async with c.execute(sql, args) as cur:
            return cur.rowcount
