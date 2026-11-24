"""The teacher's side after publishing: the live results table, the analysis of wrong answers, the CSV, the one-tap
retest for the most-missed topics, and the notes the scheduler sends (a reminder before the deadline to those who
have not started, the teacher's summary once — when everyone has finished or the deadline has passed). Every number
comes from core/analysis.py, the same function the Mini App and the demo use."""

from __future__ import annotations

from .common import Refused
from .core import analysis as A
from .core import generate as gen
from .core.clock import at_local
from .core.table import csv_text

HOUR = 3_600_000


class Results:
    async def _published(self, uid: int, tid: object, c=None) -> tuple[dict, list[dict], list[dict], list[dict]]:
        t = await self.teacher_test(uid, tid, c)
        if t["status"] != "published":
            raise Refused("not_published")
        return t, await self.questions_of(t["id"], c), await self.people_of(t["id"], c), await self.attempts_of(t["id"], c)

    async def results(self, uid: int, tid: object) -> dict:
        t, qs, people, atts = await self._published(uid, tid)
        tab = A.table(people, atts, len(qs))
        return {"id": t["id"], "title": t["title"], "code": t["code"], "deadline": t["deadline"], "minutes": t["minutes"], "parent": t["parent"],
                "total": len(qs), "now": self.now(), **tab}

    async def analysis(self, uid: int, tid: object) -> dict:
        t, qs, people, atts = await self._published(uid, tid)
        rep = A.questions_report(qs, atts)
        names = {p["id"]: p["name"] for p in people}
        tops = A.topics_report(qs, atts)
        for top in tops:
            top["people"] = [{"user": u, "name": names.get(u, "?"), "pct": v} for u, v in sorted(top["people"].items(), key=lambda kv: (kv[1], names.get(kv[0], "")))]
        for r, q in zip(rep["questions"], qs, strict=True):
            r.update(stem=q["stem"], options=q["options"], correct=q["correct"], kind=q["kind"], quote=q["quote"])
        plan = A.retest_plan(qs, atts)
        child = await self.db.one("SELECT id FROM tests WHERE parent = ? AND teacher = ?", (t["id"], uid))
        out = {"id": t["id"], "title": t["title"], "parent": t["parent"], "n": rep["n"], "k": rep["k"], "questions": rep["questions"], "topics": tops,
               "plan": {**plan, "count": len(plan["students"]), "names": [names.get(u, "?") for u in plan["students"]]}, "retest": None, "progress": None}
        if child:
            out["retest"] = child["id"]
            out["progress"] = await self._progress(t, qs, atts, child["id"])
        if t["parent"]:
            parent = await self.db.one("SELECT * FROM tests WHERE id = ?", (t["parent"],))
            out["progress"] = await self._progress(parent, await self.questions_of(parent["id"]), await self.attempts_of(parent["id"]), t["id"])
        return out

    async def _progress(self, parent: dict, qs: list[dict], atts: list[dict], child: int) -> dict:
        plan = A.retest_plan(qs, atts)
        return {**A.progress(qs, atts, plan["topics"], await self.questions_of(child), await self.attempts_of(child)), "topics": plan["topics"]}

    async def csv(self, uid: int, tid: object, labels: dict[str, str], stamp) -> tuple[str, str]:
        t, qs, people, atts = await self._published(uid, tid)
        tab = A.table(people, atts, len(qs))
        marks = {u: [None if q["id"] not in a["answers"] else int(a["answers"][q["id"]] == q["correct"]) for q in qs] for u, a in A.finals(atts).items()}
        return t["title"], csv_text(labels, tab["rows"], marks, len(qs), stamp)

    async def retest(self, uid: int, tid: object) -> tuple[dict, list[dict]]:
        """A short test from the most-missed topics, sent only to the students who missed them. Tapping it twice gives
        the same retest (no second one, no second round of notes)."""
        async with self.db.tx() as c:
            t, qs, _people, atts = await self._published(uid, tid, c)
            if t["parent"] is not None:
                raise Refused("no_retest")
            old = await self.q1(c, "SELECT id FROM tests WHERE parent = ?", (t["id"],))
            if old:
                return {"id": old["id"], "again": True}, []
            plan = A.retest_plan(qs, atts)
            if not plan["topics"] or not plan["students"]:
                raise Refused("no_retest")
            keep = [q for q in qs if q["id"] in plan["questions"]]
            src = await self.own_source(uid, t["source"], c)
            passages = {q["passage"] for q in qs if q["topic"] in plan["topics"]}
            cands = [x for x in gen.candidates(gen.analyse(src["body"], src["title"])) if x["passage"] in passages]
            fresh = gen.select(cands, max(2, min(5, 8 - len(keep))), "mixed", qs, True)
            new = sorted([*keep, *fresh], key=lambda q: (q["passage"], q["sent"], q["uid"]))[:8]
            minutes = max(5, -(-t["minutes"] * len(new) // max(1, len(qs))))
            deadline = at_local(self.today() + 1, 23 * 60 + 59)
            cur = await c.execute("INSERT INTO tests (teacher, source, grp, title, status, minutes, attempts, shuffle, reveal, rank, deadline, mix, asked, origin, "
                                  "parent, created_at, published_at) VALUES (?, ?, ?, ?, 'published', ?, 1, 1, 1, 0, ?, 'mixed', ?, 'rule', ?, ?, ?)",
                                  (uid, t["source"], t["grp"], f"{t['title']} — qayta test"[:80], minutes, deadline, len(new), t["id"], self.now(), self.now()))
            rid = cur.lastrowid
            await self._insert(c, rid, new)
            await c.executemany("INSERT INTO targets (test, user) VALUES (?, ?)", [(rid, u) for u in plan["students"]])
        notes = [{"to": u, "kind": "retest", "test": rid, "title": t["title"], "topics": plan["topics"], "count": len(new), "minutes": minutes, "deadline": deadline}
                 for u in plan["students"]]
        return {"id": rid, "again": False, "count": len(new), "students": len(plan["students"]), "topics": plan["topics"], "kept": len(keep),
                "fresh": len(fresh), "skipped": plan["skipped"]}, notes

    async def summary_if_complete(self, c, tid: int, reason: str = "all") -> list[dict]:
        """The teacher's summary, once per test: when every student has finished (or, from the scheduler, at the deadline)."""
        t = await self.q1(c, "SELECT * FROM tests WHERE id = ?", (tid,))
        people = await self.people_of(tid, c)
        atts = await self.attempts_of(tid, c)
        done = len(A.finals(atts))
        if reason == "all" and (not people or done < len(people)):
            return []
        if not await self.once(c, f"sum:{tid}"):
            return []
        qs = await self.questions_of(tid, c)
        stats = A.table(people, atts, len(qs))["stats"]
        rep = A.questions_report(qs, atts)
        flags = {f: sum(1 for r in rep["questions"] if r["flag"] == f) for f in ("key", "hard")}
        note = {"to": t["teacher"], "kind": "summary", "test": tid, "title": t["title"], "reason": reason, "done": done, "people": len(people),
                "avg": stats["avg"], "median": stats["median"], "flags": flags, "retest": t["parent"] is not None, "progress": None}
        if t["parent"]:
            parent = await self.q1(c, "SELECT * FROM tests WHERE id = ?", (t["parent"],))
            pq, pa = await self.questions_of(parent["id"], c), await self.attempts_of(parent["id"], c)
            plan = A.retest_plan(pq, pa)
            note["progress"] = A.progress(pq, pa, plan["topics"], qs, atts)
        return [note]

    async def due_notes(self) -> list[dict]:
        """Once a minute: close expired attempts, remind those who have not started, summarise tests whose deadline passed."""
        notes = await self.expire_due()
        now = self.now()
        soon = await self.db.all("SELECT id, title, deadline FROM tests WHERE status = 'published' AND deadline > ? AND deadline <= ?",
                                 (now, now + self.remind_hours * HOUR))
        for t in soon:
            async with self.db.tx() as c:
                idle = await self.qa(c, "SELECT g.user FROM targets g WHERE g.test = ? AND NOT EXISTS (SELECT 1 FROM attempts a WHERE a.test = g.test "
                                        "AND a.user = g.user) ORDER BY g.user", (t["id"],))
                for p in idle:
                    if await self.once(c, f"rem:{t['id']}:{p['user']}"):
                        notes.append({"to": p["user"], "kind": "reminder", "test": t["id"], "title": t["title"], "deadline": t["deadline"]})
        ended = await self.db.all("SELECT t.id FROM tests t WHERE t.status = 'published' AND t.deadline <= ? AND NOT EXISTS "
                                  "(SELECT 1 FROM sent s WHERE s.key = 'sum:' || t.id)", (now,))
        for t in ended:
            async with self.db.tx() as c:
                notes += await self.summary_if_complete(c, t["id"], "deadline")
        return notes
