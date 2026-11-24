"""The service: roles that never mix, classes and invites, a text to a draft and the teacher's review, publishing,
solving (server deadline, seeded order, answers saved as they go, one submit even when tapped twice at once,
auto-submit), what a student may see, teachers kept apart, the results, the analysis, the retest and the notes."""

from __future__ import annotations

import asyncio
import json

import pytest

from testustasi.common import Refused
from testustasi.core.clock import at_local, days_from_civil

from .helpers import JASUR, MADINA, NODIRA, OTHER_TEACHER, STRANGER, TEXT, TODAY, Clock, foto_draft, published, service_env


async def refused(code: str, coro) -> None:
    with pytest.raises(Refused) as err:
        await coro
    assert err.value.code == code


async def test_seed_roles_and_classes():
    async with service_env() as (svc, _clock):
        me = await svc.me(NODIRA)
        assert me["role"] == "teacher"
        classes = await svc.classes(NODIRA)
        assert classes == [{"id": 1, "name": "7-B", "students": 25, "tests": 3}]
        tests = await svc.tests(NODIRA)
        assert [t["title"] for t in tests] == ["Barg tuzilishi", "Ildiz", "Hujayra tuzilishi"] and all(t["done"] >= 23 for t in tests)
        await refused("forbidden", svc.classes(JASUR))
        await refused("role_student", svc.create_class(JASUR, "8-A"))
        await svc.create_class(OTHER_TEACHER, "8-A")
        await refused("role_teacher", svc.join_invite(OTHER_TEACHER, await svc.invite(NODIRA, 1)))
        await refused("not_found", svc.class_detail(OTHER_TEACHER, 1))
        await refused("class_exists", svc.create_class(OTHER_TEACHER, "8-A"))


async def test_invites_are_signed_and_expire_and_codes_join():
    async with service_env() as (svc, clock):
        link = await svc.invite(NODIRA, 1)
        bad = link[:-1] + ("0" if link[-1] != "0" else "1")
        await refused("invite", svc.join_invite(STRANGER, bad))
        await refused("invite", svc.join_invite(STRANGER, link.replace("g1_", "g2_")))
        joined = await svc.join_invite(STRANGER, link)
        assert joined["name"] == "7-B" and (await svc.me(STRANGER))["role"] == "student"
        clock.skip(days=15)
        await refused("invite", svc.join_invite(7778, link))
        code = (await svc.tests(NODIRA))[0]["code"]
        await svc.touch_user(7779, "Yangi", "uz")
        await refused("closed", svc.join_code(7779, code.lower()))
        await refused("code", svc.join_code(7779, "ZZZZZZ"))


async def test_text_to_draft_review_and_publish():
    async with service_env() as (svc, clock):
        await refused("too_short", svc.add_source(NODIRA, "Juda qisqa matn."))
        await refused("too_long", svc.add_source(NODIRA, "Uzun gap. " * 4000))
        await refused("forbidden", svc.add_source(JASUR, "x" * 500))
        d = await foto_draft(svc, 15)
        assert d["status"] == "draft" and len(d["questions"]) == 11 and d["origin"] == "rule" and d["asked"] == 15
        assert all(q["quote"] for q in d["questions"])
        q1, q2 = d["questions"][0], d["questions"][1]
        d = await svc.edit_question(NODIRA, d["id"], q2["id"], {"options": ["Kraxmal", "Xlorofill", "Glyukoza", "Vodorod"], "stem": q2["stem"]})
        assert d["questions"][1]["options"][3] == "Vodorod" and d["questions"][1]["edited"]
        await refused("q_distinct", svc.edit_question(NODIRA, d["id"], q2["id"], {"options": ["A", "a", "B", "C"]}))
        await refused("q_correct", svc.edit_question(NODIRA, d["id"], q2["id"], {"correct": 4}))
        d = await svc.move_question(NODIRA, d["id"], q2["id"], -1)
        assert [q["id"] for q in d["questions"][:2]] == [q2["id"], q1["id"]]
        d = await svc.delete_question(NODIRA, d["id"], q1["id"])
        assert len(d["questions"]) == 10 and [q["pos"] for q in d["questions"]] == list(range(1, 11))
        old = d["questions"][4]
        d = await svc.regen_question(NODIRA, d["id"], old["id"])
        new = d["questions"][4]
        assert new["id"] == old["id"] and new["stem"] != old["stem"] and new["stem"] not in [q["stem"] for q in d["questions"][:4]]
        await refused("no_class", svc.publish(NODIRA, d["id"]))
        for bad in ({"minutes": 0}, {"minutes": "15"}, {"attempts": 9}, {"deadline": clock.now - 1}, {"grp": 99}, {"shuffle": "yes"}, {"code": "X"}):
            with pytest.raises(Refused):
                await svc.set_settings(NODIRA, d["id"], bad)
        await refused("forbidden", svc.set_settings(OTHER_TEACHER, d["id"], {"minutes": 5}))
        await svc.create_class(OTHER_TEACHER, "8-A")
        await refused("not_found", svc.set_settings(OTHER_TEACHER, d["id"], {"minutes": 5}))
        d = await svc.set_settings(NODIRA, d["id"], {"grp": 1, "minutes": 15, "deadline": at_local(TODAY, 23 * 60 + 59)})
        view, notes = await svc.publish(NODIRA, d["id"])
        assert view["status"] == "published" and len(view["code"]) == 6 and len(notes) == 25
        assert notes[0]["kind"] == "new_test" and notes[0]["count"] == 10 and notes[0]["minutes"] == 15
        await refused("published", svc.publish(NODIRA, d["id"]))
        await refused("published", svc.edit_question(NODIRA, d["id"], new["id"], {"stem": "Boshqa savol matni?"}))
        assert JASUR in {n["to"] for n in notes}


async def test_student_never_sees_answers_before_submitting():
    async with service_env() as (svc, clock):
        t = await published(svc, clock)
        card = await svc.test_card(JASUR, t["id"])
        assert card["count"] == 10 and card["left"] == 1 and "questions" not in card
        view, _ = await svc.start(JASUR, t["id"])
        blob = json.dumps(view, ensure_ascii=False)
        for word in ("correct", "explanation", "quote", "qid", "key", "uid"):
            assert word not in blob, word
        assert all(q["quote"] not in blob for q in t["questions"])
        assert len(view["questions"]) == 10 and view["deadline_at"] == clock.now + 15 * 60_000
        await refused("not_found", svc.attempt_view(MADINA, view["attempt"]))
        await refused("not_submitted", svc.result(JASUR, t["id"]))
        await refused("not_found", svc.test_card(STRANGER, t["id"]))
        again, _ = await svc.start(JASUR, t["id"])
        assert again["questions"] == view["questions"], "a reconnect shows the same order"


async def test_solving_saves_as_it_goes_submits_once_and_reveals_mistakes():
    async with service_env() as (svc, clock):
        t = await published(svc, clock)
        view, _ = await svc.start(JASUR, t["id"])
        by_stem = {q["stem"]: q for q in t["questions"]}
        for i, item in enumerate(view["questions"]):
            q = by_stem[item["stem"]]
            want = q["options"][q["correct"]] if i < 7 else next(o for o in item["options"] if o != q["options"][q["correct"]])
            res, _ = await svc.answer(JASUR, view["attempt"], item["pos"], item["options"].index(want))
            clock.skip(seconds=40)
        assert res["answered"] == 10
        await refused("generic", svc.answer(JASUR, view["attempt"], 10, 0))
        await refused("generic", svc.answer(JASUR, view["attempt"], 0, 4))
        (r1, _), (r2, _) = await asyncio.gather(svc.submit(JASUR, view["attempt"]), svc.submit(JASUR, view["attempt"]))
        assert r1["score"] == r2["score"] == 7 and r1["pct"] == 70 and r1["grade"] == 3
        rows = await svc.db.all("SELECT id FROM attempts WHERE test = ? AND user = ? AND submitted_at IS NOT NULL", (t["id"], JASUR))
        assert len(rows) == 1
        assert r1["reveal"] and len(r1["mistakes"]) == 3 and all(m["quote"] and m["correct"] != m["chosen"] for m in r1["mistakes"])
        await refused("submitted", svc.answer(JASUR, view["attempt"], 0, 0))
        await refused("no_attempts", svc.start(JASUR, t["id"]))


async def test_time_is_kept_by_the_server_and_runs_out():
    async with service_env() as (svc, clock):
        t = await published(svc, clock, minutes=5)
        view, _ = await svc.start(JASUR, t["id"])
        await svc.answer(JASUR, view["attempt"], 0, 1)
        clock.skip(minutes=5, seconds=3)
        res, _ = await svc.answer(JASUR, view["attempt"], 1, 1)
        assert res["time_up"] is False, "a few seconds of grace for the network"
        clock.skip(seconds=10)
        res, _ = await svc.answer(JASUR, view["attempt"], 2, 1)
        assert res["time_up"] is True
        r = await svc.result(JASUR, t["id"])
        assert r["auto"] and r["seconds"] == 300, "closed at its deadline, not when noticed"
        _v2, _ = await svc.start(MADINA, t["id"])
        clock.skip(minutes=6)
        await svc.due_notes()
        assert (await svc.result(MADINA, t["id"]))["auto"]


async def test_several_attempts_hide_answers_until_the_last():
    async with service_env() as (svc, _clock):
        d = await foto_draft(svc, 5)
        await svc.set_settings(NODIRA, d["id"], {"grp": 1, "attempts": 2, "rank": True})
        t, _ = await svc.publish(NODIRA, d["id"])
        v, _ = await svc.start(JASUR, t["id"])
        r, _ = await svc.submit(JASUR, v["attempt"])
        assert r["left"] == 1 and not r["reveal"] and r["mistakes"] is None and r["rank"]["of"] == 1
        v2, _ = await svc.start(JASUR, t["id"])
        assert v2["attempt"] != v["attempt"]
        r, _ = await svc.submit(JASUR, v2["attempt"])
        assert r["left"] == 0 and r["reveal"] and len(r["mistakes"]) == 5


async def test_teachers_and_classes_stay_apart():
    async with service_env() as (svc, clock):
        t = await published(svc, clock)
        k = await svc.create_class(OTHER_TEACHER, "9-A")
        for call in (svc.results(OTHER_TEACHER, t["id"]), svc.analysis(OTHER_TEACHER, t["id"]), svc.draft_view(OTHER_TEACHER, t["id"]),
                     svc.retest(OTHER_TEACHER, t["id"]), svc.class_detail(NODIRA, k["id"])):
            await refused("not_found", call)
        await refused("forbidden", svc.results(JASUR, t["id"]))
        src = await svc.add_source(OTHER_TEACHER, TEXT["tovush"]["body"])
        await refused("not_found", svc.make_draft(NODIRA, src["id"], 5, "mixed"))
        d = await svc.make_draft(OTHER_TEACHER, src["id"], 5, "mixed")
        await refused("not_found", svc.set_settings(OTHER_TEACHER, d["id"], {"grp": 1}))


async def test_results_analysis_retest_and_notes_once():
    async with service_env() as (svc, clock):
        t = await published(svc, clock)
        qs = t["questions"]
        from testustasi.core.seedgen import simulate, students

        people = [{**s, "id": {-101: JASUR}.get(s["id"], s["id"])} for s in students()]
        traps = {2: {"kind": "pick", "option": (qs[2]["correct"] + 1) % 4, "share": 70}, 5: {"kind": "key", "option": (qs[5]["correct"] + 2) % 4}}
        sims = simulate(qs, people, "test", traps)
        notes = []
        for s in sims:
            v, _ = await svc.start(s["user"], t["id"])
            plan = {item["stem"]: item for item in v["questions"]}
            for q in qs:
                item = plan[q["stem"]]
                await svc.answer(s["user"], v["attempt"], item["pos"], item["options"].index(q["options"][s["answers"][q["id"]]]))
            clock.skip(seconds=20)
            notes += (await svc.submit(s["user"], v["attempt"]))[1]
        assert [n["kind"] for n in notes] == ["summary"] and notes[0]["done"] == 25 and notes[0]["to"] == NODIRA
        res = await svc.results(NODIRA, t["id"])
        assert res["stats"]["done"] == 25 and sum(res["stats"]["grades"].values()) == 25
        an = await svc.analysis(NODIRA, t["id"])
        flags = {r["pos"]: r["flag"] for r in an["questions"]}
        assert flags[3] == "hard" and flags[6] == "key"
        pick = an["questions"][2]["pick"]
        assert pick["option"] == (qs[2]["correct"] + 1) % 4 and pick["pct"] >= 45  # seeded: ~half the class falls for it
        _title, csv = await svc.csv(NODIRA, t["id"], {k: k for k in ("no", "name", "score", "pct", "grade", "time", "status", "at", "st_done", "st_working",
                                                                   "st_waiting")}, lambda ms: "t")
        assert csv.startswith("﻿") and csv.count("\r\n") == 26 and "Jasur" in csv
        info, rnotes = await svc.retest(NODIRA, t["id"])
        assert info["students"] == len(rnotes) == an["plan"]["count"] and 0 < info["students"] < 25
        assert {n["to"] for n in rnotes} == set(an["plan"]["students"]) and all(n["kind"] == "retest" for n in rnotes)
        again, more = await svc.retest(NODIRA, t["id"])
        assert again == {"id": info["id"], "again": True} and more == []
        await refused("not_found", svc.test_card(next(s["user"] for s in sims if s["user"] not in an["plan"]["students"]), info["id"]))
        assert len(await svc.due_notes()) == 0
        clock.at(TODAY + 1, 22 * 60)
        due = await svc.due_notes()
        assert {n["kind"] for n in due} == {"reminder"} and len(due) == info["students"]
        assert await svc.due_notes() == [], "reminded once"
        clock.at(TODAY + 2, 0)
        due = await svc.due_notes()
        assert [n["kind"] for n in due] == ["summary"] and due[0]["retest"] and due[0]["progress"]["retook"] == 0
        assert await svc.due_notes() == []


async def test_deadlines_around_tashkent_midnight_and_new_year():
    nye = days_from_civil(2026, 12, 31)
    async with service_env(Clock(at_local(nye, 23 * 60 + 40))) as (svc, clock):
        d = await foto_draft(svc, 5)
        end = at_local(nye, 23 * 60 + 59)
        await svc.set_settings(NODIRA, d["id"], {"grp": 1, "minutes": 30, "deadline": end})
        t, _ = await svc.publish(NODIRA, d["id"])
        v, _ = await svc.start(JASUR, t["id"])
        assert v["deadline_at"] == end, "the test's deadline cuts the 30 minutes"
        clock.at(nye + 1, 0)
        await refused("closed", svc.start(MADINA, t["id"]))
        notes = await svc.due_notes()
        assert any(n["kind"] == "summary" and n["reason"] == "deadline" for n in notes)
        assert (await svc.result(JASUR, t["id"]))["auto"]
