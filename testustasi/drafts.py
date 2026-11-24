"""From a source to a draft test, and the teacher's review: edit, delete, regenerate one, reorder, settings. Nothing
reaches a student before ``publish`` (in publish.py).

With an AI client the draft is asked from the model and every question goes through core/validate.py (a quote that
really occurs in the source, one correct answer, ...); rejected ones are replaced by a second request and then by the
rule-based generator, so the teacher always gets checked questions. Without a key — or past the daily limit, or when
the model fails — the rule-based generator drafts everything."""

from __future__ import annotations

import json
import logging

from .common import AIError, Refused
from .core import generate as gen
from .core.passages import split
from .core.text import clean, norm_match, normalize_source, short
from .core.validate import accept, edited

log = logging.getLogger(__name__)
MIN_CHARS = 150
MAX_CHARS = 30_000
QCOLS = ("kind", "uid", "key", "passage", "sent", "level", "topic", "stem", "options", "correct", "explanation", "quote")


def qview(q: dict) -> dict:
    return {k: q[k] for k in ("id", "pos", "kind", "level", "topic", "stem", "options", "correct", "explanation", "quote", "passage", "edited")}


class Drafts:
    async def add_source(self, uid: int, body: object, title: object = "", kind: str = "text") -> dict:
        await self.need_teacher(uid)
        if not isinstance(body, str):
            raise Refused("generic")
        text = normalize_source(body)
        if len(text) > MAX_CHARS:
            raise Refused("too_long")
        if len(text) < MIN_CHARS or not split(text):
            raise Refused("too_short")
        a = gen.analyse(text, clean(title, 80) if isinstance(title, str) else "")
        name = clean(title, 80) if isinstance(title, str) and clean(title, 80) else a["title"] or short(a["passages"][0]["sentences"][0], 60)
        async with self.db.tx() as c:
            cur = await c.execute("INSERT INTO sources (teacher, title, body, kind, created_at) VALUES (?, ?, ?, ?, ?)",
                                  (uid, name, a["body"], kind, self.now()))
        return {"id": cur.lastrowid, "title": name, "passages": len(a["passages"]), "chars": len(a["body"]),
                "possible": len(gen.select(gen.candidates(a), 20, "mixed")), "ai": self.ai is not None}

    async def own_source(self, uid: int, sid: object, c=None) -> dict:
        from .base import is_id

        if not is_id(sid):
            raise Refused("generic")
        sql = "SELECT * FROM sources WHERE id = ? AND teacher = ?"
        s = await (self.q1(c, sql, (sid, uid)) if c is not None else self.db.one(sql, (sid, uid)))
        if s is None:
            raise Refused("not_found")
        return s

    async def _ai_quota(self, uid: int) -> bool:
        """Count one AI draft for today; False when the teacher's daily limit is reached."""
        async with self.db.tx() as c:
            row = await self.q1(c, "SELECT n FROM usage WHERE teacher = ? AND day = ?", (uid, self.today()))
            if row and row["n"] >= self.ai_per_day:
                return False
            await c.execute("INSERT INTO usage (teacher, day, n) VALUES (?, ?, 1) ON CONFLICT (teacher, day) DO UPDATE SET n = n + 1", (uid, self.today()))
        return True

    async def _draft(self, uid: int, a: dict, n: int, mix: str) -> tuple[list[dict], str, str | None]:
        """(questions, origin, note): AI first when allowed, the rules for whatever is missing."""
        got: list[dict] = []
        note = None
        if self.ai is not None:
            if await self._ai_quota(uid):
                src = norm_match(a["body"])
                try:
                    got, why = accept(await self.ai.draft(a["passages"], n, mix, []), src, a["passages"], a["topics"], n)
                    if len(got) < n:
                        more, why2 = accept(await self.ai.draft(a["passages"], n - len(got), mix, [q["stem"] for q in got]), src, a["passages"],
                                            a["topics"], n - len(got), got)
                        got += more
                        why = {k: why.get(k, 0) + why2.get(k, 0) for k in {*why, *why2}}
                    if why:
                        log.info("AI draft: %d kept, rejected %s", len(got), json.dumps(why, sort_keys=True))
                except AIError as err:
                    log.warning("AI draft failed (%s); the rules draft instead", err)
                    got, note = [], "ai_failed"
            else:
                note = "ai_limit"
        rest = gen.select(gen.candidates(a), n - len(got), mix, got) if len(got) < n else []
        origin = "ai" if got and not rest else "mixed" if got else "rule"
        return got + rest, origin, note

    async def make_draft(self, uid: int, sid: object, n: object, mix: object) -> dict:
        if n not in gen.COUNTS or mix not in gen.MIXES:
            raise Refused("generic")
        await self.need_teacher(uid)
        src = await self.own_source(uid, sid)
        a = gen.analyse(src["body"], src["title"])
        qs, origin, note = await self._draft(uid, a, n, mix)
        if not qs:
            raise Refused("no_questions")
        async with self.db.tx() as c:
            cur = await c.execute("INSERT INTO tests (teacher, source, title, mix, asked, origin, note, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                                  (uid, src["id"], src["title"][:80], mix, n, origin, note, self.now()))
            tid = cur.lastrowid
            await self._insert(c, tid, qs)
        return await self.draft_view(uid, tid)

    async def _insert(self, c, tid: int, qs: list[dict], start: int = 1) -> None:
        await c.executemany(f"INSERT INTO questions (test, pos, {', '.join(QCOLS)}) VALUES ({', '.join('?' * (len(QCOLS) + 2))})",  # noqa: S608 - fixed column names
                            [(tid, start + i, *(json.dumps(q[k], ensure_ascii=False) if k == "options" else q[k] for k in QCOLS)) for i, q in enumerate(qs)])

    async def draft_view(self, uid: int, tid: object) -> dict:
        t = await self.teacher_test(uid, tid)
        src = await self.own_source(uid, t["source"])
        qs = await self.questions_of(t["id"])
        return {**{k: t[k] for k in ("id", "title", "status", "code", "minutes", "attempts", "deadline", "mix", "asked", "origin", "note", "parent",
                                     "grp", "published_at")},
                "shuffle": bool(t["shuffle"]), "reveal": bool(t["reveal"]), "rank": bool(t["rank"]), "source": src["title"],
                "questions": [qview(q) for q in qs], "classes": await self.classes(uid), "now": self.now()}

    async def _draft_question(self, uid: int, tid: object, qid: object, c) -> tuple[dict, dict]:
        t = await self.teacher_test(uid, tid, c)
        if t["status"] != "draft":
            raise Refused("published")
        q = await self.q1(c, "SELECT * FROM questions WHERE id = ? AND test = ?", (qid, t["id"]))
        if q is None:
            raise Refused("not_found")
        from .base import qrow

        return t, qrow(q)

    async def edit_question(self, uid: int, tid: object, qid: object, data: object) -> dict:
        from .base import checked

        async with self.db.tx() as c:
            t, q = await self._draft_question(uid, tid, qid, c)
            new = checked(edited, data, q)
            await c.execute("UPDATE questions SET stem = ?, options = ?, correct = ?, explanation = ?, topic = ?, edited = 1 WHERE id = ?",
                            (new["stem"], json.dumps(new["options"], ensure_ascii=False), new["correct"], new["explanation"], new["topic"], q["id"]))
        return await self.draft_view(uid, t["id"])

    async def delete_question(self, uid: int, tid: object, qid: object) -> dict:
        async with self.db.tx() as c:
            t, q = await self._draft_question(uid, tid, qid, c)
            if (await self.q1(c, "SELECT COUNT(*) AS n FROM questions WHERE test = ?", (t["id"],)))["n"] <= 1:
                raise Refused("last_question")
            await c.execute("DELETE FROM questions WHERE id = ?", (q["id"],))
            await c.execute("UPDATE questions SET pos = pos - 1 WHERE test = ? AND pos > ?", (t["id"], q["pos"]))
        return await self.draft_view(uid, t["id"])

    async def regen_question(self, uid: int, tid: object, qid: object) -> dict:
        """Replace one question with a fresh one from the same passage if possible (never one already in the test)."""
        async with self.db.tx() as c:
            t, q = await self._draft_question(uid, tid, qid, c)
            src = await self.own_source(uid, t["source"], c)
            others = [x for x in await self.questions_of(t["id"], c) if x["id"] != q["id"]]
            cands = gen.candidates(gen.analyse(src["body"], src["title"]))
            used = [*others, q]
            pick = gen.select([x for x in cands if x["passage"] == q["passage"]], 1, t["mix"], used) or gen.select(cands, 1, t["mix"], used)
            if not pick:
                raise Refused("no_more")
            new = pick[0]
            await c.execute("UPDATE questions SET kind = ?, uid = ?, key = ?, passage = ?, sent = ?, level = ?, topic = ?, stem = ?, options = ?, correct = ?, "
                            "explanation = ?, quote = ?, edited = 0 WHERE id = ?",
                            (*(json.dumps(new[k], ensure_ascii=False) if k == "options" else new[k] for k in QCOLS), q["id"]))
        return await self.draft_view(uid, t["id"])

    async def move_question(self, uid: int, tid: object, qid: object, step: object) -> dict:
        if step not in (-1, 1):
            raise Refused("generic")
        async with self.db.tx() as c:
            t, q = await self._draft_question(uid, tid, qid, c)
            other = await self.q1(c, "SELECT id, pos FROM questions WHERE test = ? AND pos = ?", (t["id"], q["pos"] + step))
            if other is not None:
                await c.execute("UPDATE questions SET pos = ? WHERE id = ?", (q["pos"], other["id"]))
                await c.execute("UPDATE questions SET pos = ? WHERE id = ?", (q["pos"] + step, q["id"]))
        return await self.draft_view(uid, t["id"])
