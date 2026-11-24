"""Load the invented class (core/seedgen.py) into an empty database: Nodira ustoz, 7-B with 25 students, the three
earlier tests with their questions, attempts and answers. Seeded people have negative ids unless the caller maps them
(the tests and the demo give the story's two people positive ids), so nobody can sign in as them."""

from __future__ import annotations

import json

QCOLS = ("kind", "uid", "key", "passage", "sent", "level", "topic", "stem", "options", "correct", "explanation", "quote")


class Seed:
    async def seed(self, world: dict, ids: dict[int, int] | None = None) -> bool:
        if await self.db.one("SELECT id FROM classes LIMIT 1"):
            return False
        ids = ids or {}
        uid = lambda x: ids.get(x, x)  # noqa: E731
        now, teacher, grp = self.now(), uid(world["teacher"]["id"]), world["group"]
        async with self.db.tx() as c:
            await c.execute("INSERT OR IGNORE INTO users (id, name, lang, role, created_at) VALUES (?, ?, 'uz', 'teacher', ?)", (teacher, world["teacher"]["name"], now))
            await c.execute("INSERT INTO classes (id, teacher, name, created_at) VALUES (?, ?, ?, ?)", (grp["id"], teacher, grp["name"], now))
            for s in world["students"]:
                await c.execute("INSERT OR IGNORE INTO users (id, name, lang, role, created_at) VALUES (?, ?, 'uz', 'student', ?)", (uid(s["id"]), s["name"], now))
                await c.execute("INSERT INTO members (grp, user, joined_at) VALUES (?, ?, ?)", (grp["id"], uid(s["id"]), now))
            for t in world["tests"]:
                text = self.texts[t["text"]]
                cur = await c.execute("INSERT INTO sources (teacher, title, body, kind, created_at) VALUES (?, ?, ?, 'seed', ?)",
                                      (teacher, text["title"], text["body"], t["published_at"]))
                await c.execute("INSERT INTO tests (id, teacher, source, grp, title, status, code, minutes, deadline, asked, created_at, published_at) "
                                "VALUES (?, ?, ?, ?, ?, 'published', ?, ?, ?, ?, ?, ?)",
                                (t["id"], teacher, cur.lastrowid, grp["id"], t["title"], t["code"], t["minutes"], t["deadline"], len(t["questions"]),
                                 t["published_at"], t["published_at"]))
                await c.executemany(f"INSERT INTO questions (id, test, pos, {', '.join(QCOLS)}) VALUES ({', '.join('?' * (len(QCOLS) + 3))})",  # noqa: S608
                                    [(q["id"], t["id"], i + 1, *(json.dumps(q[k], ensure_ascii=False) if k == "options" else q[k] for k in QCOLS))
                                     for i, q in enumerate(t["questions"])])
                await c.executemany("INSERT INTO targets (test, user) VALUES (?, ?)", [(t["id"], uid(s["id"])) for s in world["students"]])
                for a in t["attempts"]:
                    if a["submitted_at"] >= now:
                        continue
                    cur = await c.execute("INSERT INTO attempts (test, user, no, seed, started_at, deadline_at, submitted_at, score, auto) "
                                          "VALUES (?, ?, 1, 0, ?, ?, ?, ?, ?)", (t["id"], uid(a["user"]), a["started_at"], a["started_at"] + t["minutes"] * 60_000,
                                                                               a["submitted_at"], a["score"], int(a["auto"])))
                    await c.executemany("INSERT INTO answers (attempt, question, choice, at) VALUES (?, ?, ?, ?)",
                                        [(cur.lastrowid, int(q), ch, a["submitted_at"]) for q, ch in a["answers"].items()])
                await c.execute("INSERT OR IGNORE INTO sent (key, at) VALUES (?, ?)", (f"sum:{t['id']}", now))
        return True
