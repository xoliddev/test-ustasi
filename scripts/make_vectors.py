"""Regenerate shared/test_vectors.json from the Python core.

pytest checks that the file is up to date (so the Python core and the vectors never drift apart), and ``node --test``
checks the JS port against the very same vectors.

    python scripts/make_vectors.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from testustasi.core import analysis, clock, generate, numq, passages, seedgen, shuffle, table, text, uzwords, validate  # noqa: E402

OUT = ROOT / "shared" / "test_vectors.json"
TODAY = clock.days_from_civil(2026, 11, 25)
DAYS = [TODAY, clock.days_from_civil(2027, 1, 1), clock.days_from_civil(2026, 12, 31), clock.days_from_civil(2028, 2, 29)]
EXTRA = [
    # a PDF's text: every line wrapped, a word hyphenated at the end of a line, no blank lines
    "Suv aylanishi\nQuyosh issiqligi ta'sirida suv dengiz va ko'llardan bug'lanadi. Havoga ko'tarilgan bug' sovib, mayda tom-\nchilarga aylanadi va bulut hosil bo'ladi.\n"
    "Bulutdan yerga tushadigan suv yog'in deb ataladi. Yog'in yomg'ir, qor yoki do'l ko'rinishida bo'ladi. Yerga tushgan suvning bir qismi\ntuproqqa singadi, "
    "qolgani daryolar orqali yana dengizga quyiladi. Suvning tabiatda uzluksiz harakatiga suvning aylanishi deyiladi. Yer yuzasining qariyb 71 foizini suv egallaydi.",
    # Uzbek Cyrillic
    "Фотосинтез — яшил ўсимликлар ёруғлик энергияси ёрдамида органик модда ҳосил қиладиган жараён. Барг ҳужайраларидаги яшил рангли моддага хлорофилл дейилади.",
    # single line breaks between paragraphs, a list, numbers
    "Quyosh tizimi\nQuyosh tizimida 8 ta sayyora bor.\nYerga eng yaqin yulduz Quyosh hisoblanadi.\nYer Quyosh atrofini 365 kunda aylanib chiqadi.\n"
    "Oy — Yerning tabiiy yo'ldoshi.\nMerkuriy — Quyoshga eng yaqin sayyora.\nYupiter — Quyosh tizimidagi eng katta sayyora.",
    "", "Qisqa matn.", "Bu juda qisqa. U ham qisqa.",
]
WORDS = ["barglarda", "kisloroddan", "hujayralaridagi", "plastinka", "plastinkani", "modda", "moddaga", "suvdan", "organi", "atoqli", "otlar", "tuklari",
         "bo'shliqqa", "yaproqqa", "angidridni", "o'simliklar", "nomini", "bandi", "Barg", "nurini", "energiyasini", "hujayrasini", "Ҳужайра", "parda"]
NUMS = ["Fotosintez ikki bosqichda boradi.", "1771-yilda ingliz olimi Jozef Pristli o'simlik havoni tozalashini tajribada ko'rsatdi.",
        "Yer atmosferasidagi havoning qariyb 21 foizi kisloroddan iborat.", "Bitta ildiz tukining umri 10 dan 20 kungacha davom etadi.",
        "Olimlar bu yerda 1018 ta yulduzning o'rnini aniqladilar.", "Odam qulog'i 20 dan 20 000 gersgacha bo'lgan tovushlarni eshitadi.",
        "Qari hujayrada vakuola hajmning 90 foizigacha joyni egallaydi.", "1960-yillarda Orol to'rtinchi yirik ko'l edi.", "Sinfda o'n ikkita o'quvchi bor.",
        "Narx 15% ga oshdi.", "Yigirma besh kunda tayyor bo'ladi."]


def load(name: str):
    with open(ROOT / "shared" / "data" / f"{name}.json", encoding="utf-8") as fh:
        return json.load(fh)


def strip(a: dict) -> dict:
    return {"passages": a["passages"], "defs": a["defs"], "terms": a["terms"], "topics": {str(k): v for k, v in a["topics"].items()}, "title": a["title"],
            "body": a["body"]}


def gen_vectors(v: dict, texts: list[dict]) -> None:
    v["texts"] = []
    for t in [*texts, *({"id": f"extra{i}", "title": "", "body": b} for i, b in enumerate(EXTRA))]:
        a = generate.analyse(t["body"], t["title"])
        cands = generate.candidates(a)
        sel = {f"{n}:{m}": [q["uid"] for q in generate.select(cands, n, m)] for n in generate.COUNTS for m in generate.MIXES}
        some = cands[: max(1, len(cands) // 2)]
        sel["more"] = [q["uid"] for q in generate.select(cands, 6, "mixed", some)]
        sel["same"] = [q["uid"] for q in generate.select(cands, 6, "mixed", some, True)]
        v["texts"].append({"id": t["id"], "title": t["title"], "body": t["body"], "analysis": strip(a), "candidates": cands, "select": sel})
    v["stem"] = [[w, uzwords.stem(w), uzwords.case_strip(w)] for w in WORDS]
    v["inflect"] = [[b, s, uzwords.inflect(b, s)] for b in ("kislorod", "barg", "yaproq", "plastinka", "karbonat angidrid", "suv") for s in ("", "ga", "ni", "i", "idagi", "da")]
    v["numq"] = [[s, numq.find(s), numq.question(s, NUMS)] for s in NUMS]
    v["norm"] = [[s, text.norm_match(s), text.latin(s), text.normalize_source(s)] for s in
                 ["O‘simlik  havoni, tozalaydi!", "Fotosintez – jarayon", "  Ikki\r\n\r\n\r\nqator  ", "Ѕ?​nol", "Ҳужайра ва ядро"]]
    v["sentences"] = [[s, passages.sentences(s)] for s in ["Bir. Ikki! Uch? To'rt", "1771-y. Qishda bo'ldi. Keyin", "Tuz, qand va h.k. Hammasi bor.", "Kim? nima? qayer?"]]


def ai_vectors(v: dict, texts: list[dict]) -> None:
    a = generate.analyse(texts[0]["body"], texts[0]["title"])
    src = text.norm_match(a["body"])
    good = {"stem": "Xlorofill saqlovchi mayda tanachalar nima deb ataladi?", "options": ["Xloroplast", "Og'izcha", "Kraxmal", "Glyukoza"], "correct": 0,
            "explanation": "Xloroplastlar barg hujayralarida bo'ladi.", "topic": "Xloroplast", "difficulty": "oson",
            "quote": "Xlorofill saqlovchi mayda tanachalar xloroplast deb ataladi."}
    raws = [good, {**good, "stem": "Barg sirtidagi mayda teshikchalar nima deb ataladi?", "options": ["Og'izcha", "Xloroplast", "Kraxmal", "Glyukoza"],
                   "quote": "barg SIRTIDAGI mayda teshikchalar og’izcha deb ataladi", "difficulty": "qiyin"},
            {**good, "stem": "Boshqa savol?", "quote": "Bu gap matnda yo'q, lekin ishonchli ko'rinadi."},
            {**good, "stem": "Takror?", "options": ["A", "a", "B", "C"]}, {**good, "stem": "Uch variant?", "options": ["A", "B", "C"]},
            {**good, "stem": "Ikki to'g'ri?", "correct": [0, 1]}, {**good, "stem": "Mantiqiy?", "correct": True}, {**good, "stem": "Javob?", "correct": 2},
            {**good, "stem": "<b>Xlorofill</b> nima?", "options": ["<script>x</script>", "Og'izcha", "Kraxmal", "Xlorofill"], "correct": 3,
             "quote": "Barg hujayralaridagi yashil rangli moddaga xlorofill deyiladi."},
            {**good, "stem": "Xloroplast qayerda?", "quote": "Xlorofill"}, "not a dict", {**good, "stem": ""}, {**good, "stem": "Uzun " * 80},
            {**good, "stem": "Xlorofill saqlovchi mayda tanachalar nima deb ataladi?"}]
    out, why = validate.accept(raws, src, a["passages"], a["topics"], 10)
    v["ai"] = {"source": a["body"], "raws": raws, "out": out, "why": why, "checks": [[r if isinstance(r, dict) else None, _try(r, src, a)] for r in raws]}
    v["edited"] = [[d, _edit(d, out[0])] for d in ({"stem": "Yangi savol matni?"}, {"options": ["Bir", "Ikki", "Uch", "Ikki"]}, {"correct": 3},
                                                    {"topic": ""}, {"stem": 5}, {"explanation": "Izoh"}, "x")]
    v["grounded"] = [[x, q, validate.grounded(x, q)] for x, q in (("Xloroplast", "tanachalar xloroplast deb ataladi"), ("1771-yil", "1771-yilda olim"),
                                                                 ("Mitoxondriya", "tanachalar xloroplast deb ataladi"), ("21%", "havoning 21 foizi"))]


def _try(raw, src, a):
    try:
        return validate.check(raw, src, a["passages"], a["topics"])
    except validate.Rejected as err:
        return str(err)


def _edit(d, q):
    try:
        return validate.edited(d, q)
    except text.InputError as err:
        return err.code


def world_vectors(v: dict, texts: list[dict]) -> None:
    v["perm"] = [[n, s, shuffle.perm(n, s)] for n in (1, 4, 10, 25) for s in (0, 1, 42, 0xFFFFFFFF, text.h32("7:5:1"))]
    v["layout"] = [[s, shuffle.layout([11, 12, 13, 14, 15], s, sh)] for s in (shuffle.attempt_seed(7, 5, 1), shuffle.attempt_seed(7, -101, 2)) for sh in (True, False)]
    v["h32"] = [[s, text.h32(s)] for s in ("", "a", "Fotosintez", "o'simlik", "Ҳужайра", "😀", "7:5:1")]
    v["worlds"] = []
    for day in DAYS:
        w = seedgen.world(texts, day)
        people = [{"id": s["id"], "name": s["name"]} for s in w["students"]]
        reps = []
        for t in w["tests"]:
            qa = [{**a, "id": i + 1} for i, a in enumerate(t["attempts"])]
            tab = analysis.table(people, qa, len(t["questions"]))
            marks = {a["user"]: [1 if a["answers"].get(q["id"]) == q["correct"] else 0 for q in t["questions"]] for a in qa}
            csv = table.csv_text(LABELS, tab["rows"], marks, len(t["questions"]), stamp)
            reps.append({"table": tab, "questions": analysis.questions_report(t["questions"], qa), "topics": analysis.topics_report(t["questions"], qa),
                         "plan": analysis.retest_plan(t["questions"], qa), "csv": csv})
        traps = {2: {"kind": "pick", "option": 1, "share": 60}, 5: {"kind": "key", "option": 0}}
        sim = seedgen.simulate(w["tests"][0]["questions"], w["students"], f"demo:{day}", traps, 0)
        v["worlds"].append({"day": day, "world": w, "reports": reps, "sim": sim})
    v["small"] = [[p, analysis.pct(*p), analysis.rdiv(*p) if p[1] else None] for p in ((1, 3), (2, 3), (1, 2), (-1, 2), (-5, 4), (7, 10), (0, 0), (27 * 25, 100))]
    v["median"] = [[x, analysis.median(x)] for x in ([], [5], [1, 2], [70, 80, 75, 90], [3, 1, 2])]
    v["cells"] = [[x, table.cell(x)] for x in ("=SUM(A1)", "+998", "-5", "@x", "a;b", 'say "hi"', "Ism\nFamiliya", 7, None, "Jasur")]


LABELS = {"no": "№", "name": "Ism", "score": "Ball", "pct": "Foiz", "grade": "Baho", "time": "Vaqt", "status": "Holat", "at": "Topshirgan",
          "st_done": "topshirdi", "st_working": "yechyapti", "st_waiting": "boshlamagan"}


def stamp(ms: int) -> str:
    y, m, d = clock.civil(clock.local_day(ms))
    return f"{d:02d}.{m:02d}.{y} {clock.hhmm(clock.local_minute(ms))}"


def build() -> dict:
    texts = load("texts")
    v: dict = {}
    gen_vectors(v, texts)
    ai_vectors(v, texts)
    world_vectors(v, texts)
    return v


def render() -> bytes:
    return (json.dumps(build(), ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode()


if __name__ == "__main__":
    OUT.write_bytes(render())
    print("wrote", OUT.name, f"{OUT.stat().st_size // 1024} KB")
