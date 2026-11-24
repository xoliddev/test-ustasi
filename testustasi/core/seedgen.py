"""The invented class for the demo and development (the JS port is shared/seedgen.js): Nodira ustoz, her group 7-B of
25 students (Jasur among them) and three earlier tests over the last month — built from the project's own texts by
the rule-based generator, with answers simulated from each student's (invented) strength. Integer arithmetic and
FNV-1a only, so Python and JavaScript build the very same world for any "today".

``simulate`` is also what the demo uses for "the other students finish": the same function, with ``traps`` to make
a question confusing (a wrong option most students pick, or one that misleads even the strong students)."""

from __future__ import annotations

from .clock import at_local
from .generate import generate
from .text import h32

TEACHER = {"id": -1, "name": "Nodira ustoz"}
GROUP = {"id": 1, "name": "7-B", "teacher": -1}
NAMES = ["Jasur Toshpo'latov", "Madina Rahimova", "Sardor Aliyev", "Dilnoza Karimova", "Bekzod Usmonov", "Zarina Yo'ldosheva", "Otabek Nazarov",
         "Malika Saidova", "Sanjar Qodirov", "Gulnoza Ergasheva", "Jahongir Murodov", "Nilufar Hasanova", "Shohruh Ismoilov", "Kamola Tursunova",
         "Doniyor Sobirov", "Sevara Mirzayeva", "Ulug'bek Xolmatov", "Mohinur Rustamova", "Bobur Abdullayev", "Feruza Jo'rayeva", "Asadbek Nurmatov",
         "Shahzoda Qosimova", "Islom Yusupov", "Ruxshona Olimova", "Temur Ahmedov"]
ABILITY = [70, 88, 65, 91, 54, 79, 47, 83, 60, 95, 69, 58, 76, 42, 86, 63, 52, 80, 72, 45, 67, 93, 56, 74, 61]
# (text, days before today, questions, minutes): the topics the class did before photosynthesis
HISTORY = [("hujayra", 29, 8, 15), ("ildiz", 18, 8, 10), ("barg", 8, 10, 15)]
LESSON = 8 * 60 + 30


def students() -> list[dict]:
    return [{"id": -101 - i, "name": n, "ability": ABILITY[i]} for i, n in enumerate(NAMES)]


def _pick_wrong(q: dict, h: int) -> int:
    wrong = [i for i in range(4) if i != q["correct"]]
    return wrong[(0, 0, 1, 2, 1, 0)[h % 6]]


def simulate(questions: list[dict], people: list[dict], seed: str, traps: dict[int, dict] | None = None, boost: int = 0) -> list[dict]:
    """[{"user", "answers": {question id: option}, "seconds"}]: who answers what, from strength, the question's level and
    a stable per-answer number. ``traps[position]`` = {"kind": "pick", "option", "share"} or {"kind": "key", "option"}."""
    traps = traps or {}
    out = []
    for s in people:
        a = s["ability"] + boost
        answers: dict[int, int] = {}
        for i, q in enumerate(questions):
            r = h32(f"{seed}:{s['id']}:{q['id']}") % 100
            t = traps.get(i)
            if t and t["kind"] == "pick" and h32(f"pick:{seed}:{s['id']}:{q['id']}") % 100 < t["share"]:
                answers[q["id"]] = t["option"]
                continue
            if t and t["kind"] == "key":
                if a >= 72:  # the strong ones fall for the misleading option most of all
                    answers[q["id"]] = t["option"] if r < 90 else q["correct"]
                else:
                    answers[q["id"]] = t["option"] if r < 25 else q["correct"] if r < 80 else _pick_wrong(q, r)
                continue
            bias = h32(f"q:{seed}:{q['id']}") % 21 - 10
            p = max(5, min(97, 30 + (a - 50) * 3 // 2 + (2 - q["level"]) * 10 + bias))
            answers[q["id"]] = q["correct"] if r < p else _pick_wrong(q, h32(f"w:{seed}:{s['id']}:{q['id']}"))
        seconds = len(questions) * (40 + (100 - a) * 3 // 4) + h32(f"t:{seed}:{s['id']}") % 90
        out.append({"user": s["id"], "answers": answers, "seconds": seconds})
    return out


def world(texts: list[dict], today: int) -> dict:
    """The seeded teacher, group, students and earlier tests (questions, attempts with answers) relative to ``today``."""
    people = students()
    by_id = {t["id"]: t for t in texts}
    tests = []
    for k, (tid, ago, n, minutes) in enumerate(HISTORY):
        text = by_id[tid]
        qs = generate(text["body"], n, "mixed", text["title"])
        for pos, q in enumerate(qs):
            q["id"] = (k + 1) * 100 + pos + 1
        day = today - ago
        published = at_local(day, LESSON)
        attempts = []
        for s, sim in zip(people, simulate(qs, people, f"seed:{tid}"), strict=True):
            if h32(f"skip:{tid}:{s['id']}") % 25 == 0:
                continue  # one or two did not take it
            start = at_local(day, 14 * 60 + h32(f"start:{tid}:{s['id']}") % 420)
            used = min(sim["seconds"], minutes * 60 - 5)
            right = sum(1 for q in qs if sim["answers"][q["id"]] == q["correct"])
            attempts.append({"user": s["id"], "no": 1, "started_at": start, "submitted_at": start + used * 1000, "score": right,
                             "answers": sim["answers"], "auto": used == minutes * 60 - 5})
        tests.append({"id": k + 1, "text": tid, "title": text["title"], "questions": qs, "published_at": published,
                      "deadline": at_local(day + 2, 23 * 60 + 59), "minutes": minutes, "attempts": attempts, "code": _code(k + 1)})
    return {"teacher": TEACHER, "group": GROUP, "students": people, "tests": tests}


ALPHABET = "ABCDEFGHJKMNPQRSTUVWXYZ23456789"


def _code(n: int) -> str:
    h = h32(f"code:{n}")
    return "".join(ALPHABET[(h >> (5 * i)) % len(ALPHABET)] for i in range(6))
