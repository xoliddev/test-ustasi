"""A student solving a test: one attempt at a time, the deadline kept by the server (never the phone's clock), the
questions and options in the student's own seeded order, every answer saved as it is given (a reconnect loses
nothing), submitted once (a conditional UPDATE inside BEGIN IMMEDIATE: a double tap scores once), submitted
automatically at time-out. A student never receives a correct answer, an explanation or a quote before submitting —
and with attempts left, not even then."""

from __future__ import annotations

from .common import Refused
from .core import analysis as A
from .core.shuffle import attempt_seed, layout

GRACE = 5_000  # an answer sent in the last seconds still counts (network)


def _layout(t: dict, a: dict, qs: list[dict]) -> list[dict]:
    return layout([q["id"] for q in qs], a["seed"], bool(t["shuffle"]))


class Solving:
    async def my_tests(self, uid: int) -> list[dict]:
        rows = await self.db.all(
            "SELECT t.id, t.title, t.minutes, t.deadline, t.attempts, t.parent, t.published_at, k.name AS class, "
            "(SELECT COUNT(*) FROM questions q WHERE q.test = t.id) AS count FROM targets g JOIN tests t ON t.id = g.test "
            "LEFT JOIN classes k ON k.id = t.grp WHERE g.user = ? AND t.status = 'published' ORDER BY t.published_at DESC, t.id DESC LIMIT 60", (uid,))
        mine = await self.db.all("SELECT test, COUNT(*) AS n, SUM(submitted_at IS NULL) AS open, MAX(CASE WHEN submitted_at IS NOT NULL THEN id END) AS last "
                                 "FROM attempts WHERE user = ? GROUP BY test", (uid,))
        by = {m["test"]: m for m in mine}
        last_ids = [m["last"] for m in mine if m["last"]]
        scores = {r["id"]: r for r in await self.db.all(f"SELECT id, score FROM attempts WHERE id IN ({','.join('?' * len(last_ids))})", tuple(last_ids))} \
            if last_ids else {}  # noqa: S608 - placeholders only
        out = []
        for r in rows:
            m = by.get(r["id"])
            closed = r["deadline"] is not None and r["deadline"] <= self.now()
            done = m is not None and m["last"] is not None
            status = "working" if m and m["open"] else "done" if done else "closed" if closed else "new"
            item = {**r, "status": status, "retest": r["parent"] is not None}
            if done:
                item["score"] = scores[m["last"]]["score"]
                item["pct"] = A.pct(item["score"], r["count"])
            out.append(item)
        return out

    async def test_card(self, uid: int, tid: object) -> dict:
        t = await self.student_test(uid, tid)
        n = (await self.db.one("SELECT COUNT(*) AS n FROM questions WHERE test = ?", (t["id"],)))["n"]
        att = await self.db.all("SELECT id, submitted_at FROM attempts WHERE test = ? AND user = ? ORDER BY no", (t["id"], uid))
        used = sum(1 for a in att if a["submitted_at"] is not None)
        open_ = next((a["id"] for a in att if a["submitted_at"] is None), None)
        closed = t["deadline"] is not None and t["deadline"] <= self.now()
        return {"id": t["id"], "title": t["title"], "count": n, "minutes": t["minutes"], "deadline": t["deadline"], "attempts": t["attempts"], "used": used,
                "left": max(0, t["attempts"] - used), "open": open_, "closed": closed, "done": used > 0, "now": self.now(), "retest": t["parent"] is not None}

    async def _own_attempt(self, c, uid: int, aid: object) -> tuple[dict, dict]:
        from .base import is_id

        if not is_id(aid):
            raise Refused("generic")
        a = await self.q1(c, "SELECT * FROM attempts WHERE id = ? AND user = ?", (aid, uid))
        if a is None:
            raise Refused("not_found")
        return a, await self.student_test(uid, a["test"], c)

    async def start(self, uid: int, tid: object) -> tuple[dict, list[dict]]:
        """The open attempt (after a reconnect) or a new one; notes when an expired one had to be closed first."""
        notes: list[dict] = []
        async with self.db.tx() as c:
            t = await self.student_test(uid, tid, c)
            a = await self.q1(c, "SELECT * FROM attempts WHERE test = ? AND user = ? AND submitted_at IS NULL", (t["id"], uid))
            if a is not None and self.now() > a["deadline_at"] + GRACE:
                notes += await self._finalize(c, a, auto=True)
                a = None
            if a is None:
                if t["deadline"] is not None and t["deadline"] <= self.now():
                    raise Refused("closed")
                done = await self.q1(c, "SELECT COUNT(*) AS n, COALESCE(MAX(no), 0) AS top FROM attempts WHERE test = ? AND user = ?", (t["id"], uid))
                if done["n"] >= t["attempts"]:
                    raise Refused("no_attempts")
                no = done["top"] + 1
                limit = self.now() + t["minutes"] * 60_000
                ends = min(limit, t["deadline"]) if t["deadline"] is not None else limit
                cur = await c.execute("INSERT INTO attempts (test, user, no, seed, started_at, deadline_at) VALUES (?, ?, ?, ?, ?, ?)",
                                      (t["id"], uid, no, attempt_seed(t["id"], uid, no), self.now(), ends))
                a = await self.q1(c, "SELECT * FROM attempts WHERE id = ?", (cur.lastrowid,))
        return await self.attempt_view(uid, a["id"]), notes

    async def attempt_view(self, uid: int, aid: object) -> dict:
        """What the student's screen needs — and nothing more: the stems and the options in their order, the saved
        choices, the server's deadline. No correct answers, no explanations, no quotes, no question ids."""
        async with self.db.tx() as c:
            a, t = await self._own_attempt(c, uid, aid)
            qs = await self.questions_of(t["id"], c)
            ans = {r["question"]: r["choice"] for r in await self.qa(c, "SELECT question, choice FROM answers WHERE attempt = ?", (a["id"],))}
        by = {q["id"]: q for q in qs}
        items, chosen = [], {}
        for pos, item in enumerate(_layout(t, a, qs)):
            q = by[item["qid"]]
            items.append({"pos": pos, "stem": q["stem"], "options": [q["options"][k] for k in item["opts"]]})
            if item["qid"] in ans:
                chosen[str(pos)] = item["opts"].index(ans[item["qid"]])
        return {"attempt": a["id"], "test": t["id"], "title": t["title"], "no": a["no"], "deadline_at": a["deadline_at"], "now": self.now(),
                "submitted": a["submitted_at"] is not None, "questions": items, "answers": chosen}

    async def answer(self, uid: int, aid: object, pos: object, choice: object) -> tuple[dict, list[dict]]:
        """Save one choice (display position and display option); past the deadline the attempt is closed instead and the
        answer is not taken ({"time_up": true})."""
        if not isinstance(pos, int) or isinstance(pos, bool) or not isinstance(choice, int) or isinstance(choice, bool) or not 0 <= choice <= 3 or pos < 0:
            raise Refused("generic")
        async with self.db.tx() as c:
            a, t = await self._own_attempt(c, uid, aid)
            if a["submitted_at"] is not None:
                raise Refused("submitted")
            if self.now() > a["deadline_at"] + GRACE:
                return {"time_up": True, "test": t["id"]}, await self._finalize(c, a, auto=True)
            plan = _layout(t, a, await self.questions_of(t["id"], c))
            if pos >= len(plan):
                raise Refused("generic")
            item = plan[pos]
            await c.execute("INSERT INTO answers (attempt, question, choice, at) VALUES (?, ?, ?, ?) ON CONFLICT (attempt, question) DO UPDATE "
                            "SET choice = excluded.choice, at = excluded.at", (a["id"], item["qid"], item["opts"][choice], self.now()))
            n = (await self.q1(c, "SELECT COUNT(*) AS n FROM answers WHERE attempt = ?", (a["id"],)))["n"]
        return {"pos": pos, "choice": choice, "answered": n, "total": len(plan), "time_up": False}, []

    async def _finalize(self, c, a: dict, auto: bool) -> list[dict]:
        """Score and close an open attempt, once. A late one closes at its deadline, not at the moment it is noticed."""
        qs = await self.questions_of(a["test"], c)
        ans = {r["question"]: r["choice"] for r in await self.qa(c, "SELECT question, choice FROM answers WHERE attempt = ?", (a["id"],))}
        at = min(self.now(), a["deadline_at"]) if auto else self.now()
        changed = await self.run(c, "UPDATE attempts SET submitted_at = ?, score = ?, auto = ? WHERE id = ? AND submitted_at IS NULL",
                                 (at, A.score(qs, ans), int(auto), a["id"]))
        if changed != 1:
            return []
        return await self.summary_if_complete(c, a["test"])

    async def submit(self, uid: int, aid: object) -> tuple[dict, list[dict]]:
        async with self.db.tx() as c:
            a, t = await self._own_attempt(c, uid, aid)
            notes = await self._finalize(c, a, auto=self.now() > a["deadline_at"] + GRACE)
        return await self.result(uid, t["id"]), notes

    async def expire_due(self) -> list[dict]:
        """Auto-submit every attempt whose time is up (the scheduler, once a minute)."""
        notes: list[dict] = []
        due = await self.db.all("SELECT * FROM attempts WHERE submitted_at IS NULL AND deadline_at + ? < ? ORDER BY id LIMIT 500", (GRACE, self.now()))
        for a in due:
            async with self.db.tx() as c:
                notes += await self._finalize(c, a, auto=True)
        return notes

    async def result(self, uid: int, tid: object) -> dict:
        t = await self.student_test(uid, tid)
        qs = await self.questions_of(t["id"])
        atts = [a for a in await self.attempts_of(t["id"]) if a["user"] == uid and a["submitted_at"] is not None]
        if not atts:
            raise Refused("not_submitted")
        a = atts[-1]
        left = max(0, t["attempts"] - len(await self.db.all("SELECT id FROM attempts WHERE test = ? AND user = ?", (t["id"], uid))))
        closed = t["deadline"] is not None and t["deadline"] <= self.now()
        pc = A.pct(a["score"], len(qs))
        out = {"test": t["id"], "title": t["title"], "score": a["score"], "total": len(qs), "pct": pc, "grade": A.grade(pc), "auto": bool(a["auto"]),
               "seconds": max(0, (a["submitted_at"] - a["started_at"]) // 1000), "left": left, "closed": closed, "reveal": False, "rank": None,
               "mistakes": None, "retest": t["parent"] is not None}
        if t["rank"]:
            finals = A.finals(await self.attempts_of(t["id"]))
            out["rank"] = {"place": 1 + sum(1 for f in finals.values() if f["score"] > a["score"]), "of": len(finals)}
        if t["reveal"] and (left == 0 or closed):
            out["reveal"] = True
            plan = _layout(t, a, qs)
            by = {q["id"]: q for q in qs}
            out["mistakes"] = [{"n": i + 1, "stem": by[p["qid"]]["stem"], "chosen": by[p["qid"]]["options"][a["answers"][p["qid"]]] if p["qid"] in a["answers"]
                                else None, "correct": by[p["qid"]]["options"][by[p["qid"]]["correct"]], "explanation": by[p["qid"]]["explanation"],
                                "quote": by[p["qid"]]["quote"]} for i, p in enumerate(plan) if a["answers"].get(p["qid"]) != by[p["qid"]]["correct"]]
        return out
