"""A draft's settings and "Nashr qilish": the test gets its class, its code and its students, and each student is
notified. Settings are checked on the server: a time limit of 1–180 minutes, 1–5 attempts, a deadline in the future
(and within 60 days), a class of this teacher."""

from __future__ import annotations

from .common import Refused
from .groups import new_code

DAY = 86_400_000
FLAGS = ("shuffle", "reveal", "rank")


class Publish:
    async def set_settings(self, uid: int, tid: object, data: object) -> dict:
        from .base import is_id

        if not isinstance(data, dict) or not data or len(data) > 8:
            raise Refused("generic")
        async with self.db.tx() as c:
            t = await self.teacher_test(uid, tid, c)
            changes: dict[str, object] = {}
            for key, value in data.items():
                if key in FLAGS:
                    if not isinstance(value, bool):
                        raise Refused("generic")
                    changes[key] = int(value)
                    continue
                if t["status"] != "draft":
                    raise Refused("published")
                if key == "minutes":
                    if not isinstance(value, int) or isinstance(value, bool) or not 1 <= value <= 180:
                        raise Refused("minutes")
                    changes[key] = value
                elif key == "attempts":
                    if not isinstance(value, int) or isinstance(value, bool) or not 1 <= value <= 5:
                        raise Refused("attempts")
                    changes[key] = value
                elif key == "deadline":
                    if value is not None and (not isinstance(value, int) or isinstance(value, bool) or not self.now() + 5 * 60_000 <= value <= self.now() + 60 * DAY):
                        raise Refused("deadline")
                    changes[key] = value
                elif key == "grp":
                    if value is not None:
                        if not is_id(value):
                            raise Refused("generic")
                        await self.own_class(uid, value, c)
                    changes[key] = value
                elif key == "title":
                    from .base import checked
                    from .core.text import checked_text

                    changes[key] = checked(checked_text, value, 2, 80, "title")
                else:
                    raise Refused("generic")
            sets = ", ".join(f"{k} = ?" for k in changes)
            await c.execute(f"UPDATE tests SET {sets} WHERE id = ? AND teacher = ?", (*changes.values(), t["id"], uid))  # noqa: S608 - keys are fixed names
        return await self.draft_view(uid, t["id"])

    async def publish(self, uid: int, tid: object) -> tuple[dict, list[dict]]:
        """Draft -> published for the chosen class: a unique code, the class's students as targets, one note each."""
        async with self.db.tx() as c:
            t = await self.teacher_test(uid, tid, c)
            if t["status"] != "draft":
                raise Refused("published")
            if t["grp"] is None:
                raise Refused("no_class")
            k = await self.own_class(uid, t["grp"], c)
            if t["deadline"] is not None and t["deadline"] <= self.now():
                raise Refused("deadline")
            n = (await self.q1(c, "SELECT COUNT(*) AS n FROM questions WHERE test = ?", (t["id"],)))["n"]
            if n == 0:
                raise Refused("no_questions")
            code = new_code()
            while await self.q1(c, "SELECT id FROM tests WHERE code = ?", (code,)):
                code = new_code()
            if await self.run(c, "UPDATE tests SET status = 'published', code = ?, published_at = ? WHERE id = ? AND status = 'draft'",
                              (code, self.now(), t["id"])) != 1:
                raise Refused("published")
            await c.execute("INSERT OR IGNORE INTO targets (test, user) SELECT ?, user FROM members WHERE grp = ?", (t["id"], k["id"]))
            people = await self.qa(c, "SELECT user FROM targets WHERE test = ? ORDER BY user", (t["id"],))
        notes = [{"to": p["user"], "kind": "new_test", "test": t["id"], "title": t["title"], "count": n, "minutes": t["minutes"], "deadline": t["deadline"],
                  "class": k["name"]} for p in people]
        return await self.draft_view(uid, t["id"]), notes

    async def tests(self, uid: int) -> list[dict]:
        """The teacher's tests, newest first, with how many students got and finished each."""
        await self.need_teacher(uid)
        return await self.db.all(
            "SELECT t.id, t.title, t.status, t.code, t.minutes, t.deadline, t.parent, t.created_at, t.published_at, k.name AS class, "
            "(SELECT COUNT(*) FROM questions q WHERE q.test = t.id) AS questions, (SELECT COUNT(*) FROM targets g WHERE g.test = t.id) AS people, "
            "(SELECT COUNT(DISTINCT a.user) FROM attempts a WHERE a.test = t.id AND a.submitted_at IS NOT NULL) AS done "
            "FROM tests t LEFT JOIN classes k ON k.id = t.grp WHERE t.teacher = ? ORDER BY COALESCE(t.published_at, t.created_at) DESC, t.id DESC LIMIT 100",
            (uid,))
