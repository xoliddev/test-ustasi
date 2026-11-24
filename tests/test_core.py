"""The pure core: the rule-based generator on the story's text and on ordinary texts a teacher would paste, the quote
check, the seeded shuffle, the analysis in integer math, the CSV, and the vectors the JS port is checked against."""

from __future__ import annotations

import sys

from testustasi.core import analysis as A
from testustasi.core import generate as G
from testustasi.core.shuffle import attempt_seed, layout, perm
from testustasi.core.table import cell, csv_text
from testustasi.core.text import norm_match
from testustasi.core.validate import accept, grounded, occurs

from .helpers import FOTO, ROOT, TEXT

sys.path.insert(0, str(ROOT / "scripts"))


def test_vectors_are_up_to_date():
    import make_vectors

    assert make_vectors.render() == (ROOT / "shared" / "test_vectors.json").read_bytes(), "run: python scripts/make_vectors.py"


def test_the_story_text_gives_eleven_checked_questions_when_fifteen_are_asked():
    qs = G.generate(FOTO, 15, "mixed", "Fotosintez")
    assert len(qs) == 11, "fewer questions rather than bad ones"
    body = norm_match(G.analyse(FOTO)["body"])
    for q in qs:
        assert len(q["options"]) == 4 and len({norm_match(o) for o in q["options"]}) == 4
        assert 0 <= q["correct"] <= 3 and occurs(q["quote"], body), q["stem"]
        assert grounded(q["options"][q["correct"]], q["quote"]) or q["kind"] == "rev", q["stem"]  # "2" is grounded by "ikki bosqichda"
    stems = [q["stem"] for q in qs]
    assert "Xlorofill saqlovchi mayda tanachalar nima deb ataladi?" in stems
    assert "Fotosintez necha bosqichda boradi?" in stems
    assert any(s.startswith("Qaysi yilda ingliz olimi Jozef Pristli") for s in stems)
    assert {q["kind"] for q in qs} == {"def", "gap", "num", "rev"}
    assert len({q["passage"] for q in qs}) == 6, "every passage is asked about"
    assert [len(G.generate(FOTO, n)) for n in (5, 10, 20)] == [5, 10, 11]


def test_ordinary_texts_from_other_subjects():
    hist = G.generate(TEXT["ulugbek"]["body"], 10)
    assert {"Ulug'bek qaysi yilda Samarqandda madrasa qurdirgan?", "Rasadxona xarobalarini qaysi yilda arxeolog Vasiliy Vyatkin topgan?"} <= {q["stem"] for q in hist}
    year = next(q for q in hist if q["stem"].startswith("Ulug'bek qaysi"))
    assert year["options"][year["correct"]] == "1420-yil" and all(o.endswith("-yil") for o in year["options"])
    phys = {q["stem"]: q for q in G.generate(TEXT["tovush"]["body"], 10)}
    assert "Tovushning to'siqdan qaytishi nima deb ataladi?" in phys
    assert phys["Suvda tovush havodagiga qaraganda taxminan necha marta tez tarqaladi?"]["options"] == ["5", "4", "3", "6"]
    bio = {q["stem"] for q in G.generate(TEXT["ildiz"]["body"], 10)}
    assert "Ildiz uchida joylashgan juda mayda o'simtalar nima deb ataladi?" in bio
    lang = {q["stem"] for q in G.generate(TEXT["ot"]["body"], 10)}
    assert "Bir xil narsalarning umumiy nomini bildirgan otlarga nima deyiladi?" in lang


def test_a_definition_without_ga_before_the_term():
    text = ("Suv aylanishi — suvning tabiatda uzluksiz harakatlanish jarayoni. Suvning bug'ga aylanishi bug'lanish deb ataladi. "
            "Bug'ning suyuqlikka aylanishi kondensatsiya deyiladi. Bulutdan yerga tushadigan suv yog'in deb ataladi. "
            "Bitta bandda bitta plastinka bo'lsa, oddiy barg deyiladi.")
    qs = {q["stem"]: q for q in G.generate(text, 10)}
    q = qs["Bug'ning suyuqlikka aylanishi nima deyiladi?"]
    assert q["options"][q["correct"]] == "Kondensatsiya" and q["quote"] == "Bug'ning suyuqlikka aylanishi kondensatsiya deyiladi."
    assert not any("bo'lsa" in s for s in qs), "a condition stays skipped"


def test_quality_rules_skip_what_would_be_a_bad_question():
    text = ("Bu jarayon juda muhim. U har kuni takrorlanadi. Suv bo'lmasa, o'simlik quriydi. Mitoz — hujayraning bo'linish jarayoni. "
            "Meyoz — jinsiy hujayralarning hosil bo'lish jarayoni. Bitta hujayradan 10 dan 20 tagacha hujayra hosil bo'ladi.")
    stems = [q["stem"] for q in G.generate(text, 20)]
    assert not any(s.startswith(("Bo'sh joyga mos javobni tanlang: «Bu", "Bo'sh joyga mos javobni tanlang: «U")) for s in stems), "needs the previous sentence"
    assert not any("bo'lmasa" in s for s in stems), "a condition: other options could be true too"
    assert not any("10 dan" in s or "necha" in s for s in stems), "a range is not one number"
    assert G.generate("Qisqa matn.", 10) == [] and G.generate("", 5) == []


def test_pdf_like_and_cyrillic_input():
    pdf = ("Suv aylanishi\nQuyosh issiqligi ta'sirida suv dengiz va ko'llardan bug'lanadi. Havoga ko'tarilgan bug' sovib, mayda tom-\nchilarga aylanadi.\n"
           "Bulutdan yerga tushadigan suv yog'in deb ataladi. Yer yuzasining qariyb 71 foizini suv egallaydi.")
    a = G.analyse(pdf)
    assert "tomchilarga" in a["body"] and a["passages"][0]["heading"] == "Suv aylanishi"
    assert any(q["stem"] == "Yer yuzasining qariyb necha foizini suv egallaydi?" for q in G.generate(pdf, 10))
    cyr = G.analyse("Фотосинтез — яшил ўсимликлар ёруғлик ёрдамида органик модда ҳосил қиладиган жараён.")
    assert cyr["body"].startswith("Fotosintez — yashil o'simliklar") and cyr["defs"][0]["term"] == "Fotosintez"


def test_ai_questions_need_a_real_quote_and_one_correct_answer():
    a = G.analyse(FOTO)
    src = norm_match(a["body"])
    base = {"stem": "Xlorofill saqlovchi mayda tanachalar nima deb ataladi?", "options": ["Xloroplast", "Og'izcha", "Kraxmal", "Glyukoza"], "correct": 0,
            "quote": "Xlorofill saqlovchi mayda tanachalar xloroplast deb ataladi.", "topic": "Xloroplast"}
    bad = [{**base, "quote": "Matnda bunday gap yo'q, lekin ishonarli."}, {**base, "correct": [0, 1]}, {**base, "correct": True},
           {**base, "options": ["A", "a", "B", "C"]}, {**base, "options": base["options"][:3]}, {**base, "correct": 2}, {**base, "quote": "Xlorofill"},
           "{}", {**base, "stem": 7}]
    out, why = accept([*bad, base, {**base, "quote": "XLOROFILL  saqlovchi mayda tanachalar, xloroplast deb ataladi"}], src, a["passages"], a["topics"], 10)
    assert len(out) == 1, "only the grounded question; the copy with another quote is a duplicate"
    assert why == {"quote": 2, "correct": 2, "grounded": 1, "distinct": 1, "options": 1, "shape": 1, "stem": 1, "duplicate": 1}
    q = out[0]
    assert q["options"][q["correct"]] == "Xloroplast" and q["kind"] == "ai" and q["passage"] == 2


def test_seeded_shuffle_is_stable_and_per_student():
    assert perm(10, 42) == perm(10, 42) and sorted(perm(10, 42)) == list(range(10))
    a, b = layout(list(range(1, 11)), attempt_seed(5, 1, 1)), layout(list(range(1, 11)), attempt_seed(5, 2, 1))
    assert a != b and sorted(x["qid"] for x in a) == list(range(1, 11))
    assert layout([1, 2, 3], 9, False) == [{"qid": i, "opts": [0, 1, 2, 3]} for i in (1, 2, 3)]


def _att(user: int, answers: dict, score: int, secs: int = 300) -> dict:
    return {"id": user, "user": user, "started_at": 0, "submitted_at": secs * 1000, "score": score, "answers": answers, "auto": False}


def test_analysis_flags_and_integer_math():
    qs = [{"id": i, "topic": "T1" if i < 3 else "T2", "correct": 0} for i in range(1, 5)]
    atts = []
    for u in range(1, 11):
        strong = u <= 3
        ans = {1: 0, 2: 0 if u <= 8 else 1, 3: 2 if strong else (0 if u % 2 else 1), 4: 1 if 4 <= u <= 9 else 0}
        atts.append(_att(u, ans, sum(1 for q in qs if ans[q["id"]] == 0) + (10 if strong else 0)))
    rep = {r["id"]: r for r in A.questions_report(qs, atts)["questions"]}
    assert rep[1]["flag"] == "easy" and rep[1]["pct"] == 100
    assert rep[3]["flag"] == "key" and rep[3]["top"] == 0, "the strongest three all picked C"
    assert rep[4]["flag"] == "hard" and rep[4]["pick"] == {"option": 1, "letter": "B", "pct": 60}
    assert rep[2]["flag"] is None and rep[2]["pct"] == 80
    assert [A.pct(1, 3), A.pct(2, 3), A.pct(1, 2), A.rdiv(-1, 2), A.grade(86), A.grade(85), A.grade(55), A.median([70, 80, 75, 90])] == [33, 67, 50, -1, 5, 4, 2, 78]
    plan = A.retest_plan(qs, atts)
    assert plan["topics"] == ["T2"] and plan["questions"] == [4] and plan["skipped"] == [3] and plan["students"] == [4, 5, 6, 7, 8, 9]
    assert plan["before"] == 35
    again = [_att(u, {4: 0}, 1) for u in plan["students"]]
    assert A.progress(qs, atts, ["T2"], [qs[3]], again) == {"before": 35, "after": 71, "retook": 6}, "10 right of 14: six retakes + the others' first results"


def test_csv_opens_in_excel():
    rows = [{"user": 1, "name": "=HYPERLINK(\"x\")", "status": "done", "score": 7, "pct": 70, "grade": 3, "seconds": 452, "at": 1},
            {"user": 2, "name": "Ali; Vali", "status": "waiting", "score": None, "pct": None, "grade": None, "seconds": None, "at": None}]
    labels = {"no": "№", "name": "Ism", "score": "Ball", "pct": "Foiz", "grade": "Baho", "time": "Vaqt", "status": "Holat", "at": "Vaqti",
              "st_done": "topshirdi", "st_working": "yechyapti", "st_waiting": "boshlamagan"}
    out = csv_text(labels, rows, {1: [1, 0, None]}, 3, lambda ms: "25.11.2026 09:20")
    assert out.startswith("﻿№;Ism;Ball") and out.endswith("\r\n")
    assert "1;'=HYPERLINK(\"\"x\"\");7;70;3;7:32;topshirdi;25.11.2026 09:20;1;0;" in out.replace('"\'', "'").replace('"\r', "\r") or "'=HYPERLINK" in out
    assert '"Ali; Vali"' in out and cell("-5") == "'-5" and cell(7) == "7"
