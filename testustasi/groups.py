"""Classes and how students get in: a teacher's signed, expiring invite link (``/start g<class>_<expiry>_<signature>``)
or a published test's 6-character code. Joining makes the person a student (a teacher cannot join) and gives them
the class's open tests."""

from __future__ import annotations

import hashlib
import hmac
import re
import secrets

from .common import Refused
from .core.seedgen import ALPHABET
from .core.text import checked_text

INVITE = re.compile(r"g(\d{1,9})_(\d{1,7})_([0-9a-f]{16})")
CODE = re.compile(f"[{ALPHABET}]{{6}}")
HOUR = 3_600_000


def new_code() -> str:
    return "".join(secrets.choice(ALPHABET) for _ in range(6))


def norm_code(text: object) -> str | None:
    """"ab3k9q", " AB3K9Q " -> "AB3K9Q"; anything else -> None."""
    s = str(text or "").strip().upper()
    return s if CODE.fullmatch(s) else None


class Groups:
    def _sign(self, gid: int, exp: int) -> str:
        return hmac.new(self.invite_secret, f"grp:{gid}:{exp}".encode(), hashlib.sha256).hexdigest()[:16]

    async def create_class(self, uid: int, name: object) -> dict:
        from .base import checked

        title = checked(checked_text, name, 1, 24, "class_name")
        async with self.db.tx() as c:
            await self.set_role(uid, "teacher", c)
            if await self.q1(c, "SELECT id FROM classes WHERE teacher = ? AND name = ?", (uid, title)):
                raise Refused("class_exists")
            if (await self.q1(c, "SELECT COUNT(*) AS n FROM classes WHERE teacher = ?", (uid,)))["n"] >= 30:
                raise Refused("too_many")
            cur = await c.execute("INSERT INTO classes (teacher, name, created_at) VALUES (?, ?, ?)", (uid, title, self.now()))
        return {"id": cur.lastrowid, "name": title, "students": 0}

    async def classes(self, uid: int) -> list[dict]:
        await self.need_teacher(uid)
        return await self.db.all(
            "SELECT k.id, k.name, (SELECT COUNT(*) FROM members m WHERE m.grp = k.id) AS students, "
            "(SELECT COUNT(*) FROM tests t WHERE t.grp = k.id AND t.status = 'published') AS tests FROM classes k WHERE k.teacher = ? ORDER BY k.name, k.id",
            (uid,))

    async def own_class(self, uid: int, gid: object, c=None) -> dict:
        from .base import is_id

        if not is_id(gid):
            raise Refused("generic")
        await self.need_teacher(uid, c)
        sql = "SELECT * FROM classes WHERE id = ? AND teacher = ?"
        k = await (self.q1(c, sql, (gid, uid)) if c is not None else self.db.one(sql, (gid, uid)))
        if k is None:
            raise Refused("not_found")
        return k

    async def class_detail(self, uid: int, gid: object) -> dict:
        k = await self.own_class(uid, gid)
        students = await self.db.all("SELECT u.id, u.name, m.joined_at FROM members m JOIN users u ON u.id = m.user WHERE m.grp = ? ORDER BY u.name, u.id",
                                     (k["id"],))
        return {"id": k["id"], "name": k["name"], "students": students}

    async def invite(self, uid: int, gid: object) -> str:
        """A deep-link payload that lets anyone with it join the class for ``invite_days`` days."""
        k = await self.own_class(uid, gid)
        exp = self.now() // HOUR + self.invite_days * 24
        return f"g{k['id']}_{exp}_{self._sign(k['id'], exp)}"

    async def _join(self, c, uid: int, gid: int) -> int:
        """Membership plus the class's open tests; returns how many tests the student got."""
        await self.set_role(uid, "student", c)
        await c.execute("INSERT OR IGNORE INTO members (grp, user, joined_at) VALUES (?, ?, ?)", (gid, uid, self.now()))
        return await self.run(c, "INSERT OR IGNORE INTO targets (test, user) SELECT id, ? FROM tests WHERE grp = ? AND status = 'published' "
                                 "AND parent IS NULL AND (deadline IS NULL OR deadline > ?)", (uid, gid, self.now()))

    async def join_invite(self, uid: int, payload: str) -> dict:
        m = INVITE.fullmatch(payload or "")
        if not m:
            raise Refused("invite")
        gid, exp = int(m[1]), int(m[2])
        if not hmac.compare_digest(self._sign(gid, exp), m[3]) or exp * HOUR < self.now():
            raise Refused("invite")
        async with self.db.tx() as c:
            k = await self.q1(c, "SELECT * FROM classes WHERE id = ?", (gid,))
            if k is None:
                raise Refused("invite")
            got = await self._join(c, uid, gid)
            teacher = await self.q1(c, "SELECT name FROM users WHERE id = ?", (k["teacher"],))
        return {"id": gid, "name": k["name"], "teacher": teacher["name"] if teacher else "", "tests": got}

    async def join_code(self, uid: int, text: object) -> dict:
        """A test's code: join its class (if not yet) and get the test."""
        code = norm_code(text)
        if code is None:
            raise Refused("code")
        async with self.db.tx() as c:
            t = await self.q1(c, "SELECT * FROM tests WHERE code = ? AND status = 'published' AND parent IS NULL", (code,))
            if t is None or t["grp"] is None:
                raise Refused("code")
            if t["deadline"] is not None and t["deadline"] <= self.now():
                raise Refused("closed")
            await self._join(c, uid, t["grp"])
            await c.execute("INSERT OR IGNORE INTO targets (test, user) VALUES (?, ?)", (t["id"], uid))
            k = await self.q1(c, "SELECT name FROM classes WHERE id = ?", (t["grp"],))
        return {"test": t["id"], "title": t["title"], "class": k["name"]}

    async def my_classes(self, uid: int) -> list[dict]:
        return await self.db.all("SELECT k.id, k.name, u.name AS teacher FROM members m JOIN classes k ON k.id = m.grp JOIN users u ON u.id = k.teacher "
                                 "WHERE m.user = ? ORDER BY k.name", (uid,))
