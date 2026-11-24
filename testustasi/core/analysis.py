"""Scores, the results table's numbers and the analysis of wrong answers, in integer math only (the JS port is
shared/analysis.js, checked by shared vectors, so the teacher's Mini App, the bot's summary and the demo show the same
numbers).

* a percentage is round-half-up of 100 × part / whole;
* the grade is the school's five-point scale (86 % and up — 5, 71 % — 4, 56 % — 3, below — 2);
* discrimination compares the top 27 % of students (by score) with the bottom 27 %;
* flags: "key" (strong students got it wrong too: the question or its key may be wrong), "hard" (most got it wrong;
  with the wrong option most of them picked), "easy" (nearly everyone got it right). Flags need at least 5 results."""

from __future__ import annotations

LETTERS = "ABCD"
MIN_FLAGS = 5


def rdiv(a: int, b: int) -> int:
    """a / b rounded half away from zero, b > 0."""
    return -((-2 * a + b) // (2 * b)) if a < 0 else (2 * a + b) // (2 * b)


def pct(part: int, whole: int) -> int:
    return rdiv(100 * part, whole) if whole > 0 else 0


def grade(p: int) -> int:
    return 5 if p >= 86 else 4 if p >= 71 else 3 if p >= 56 else 2


def median(values: list[int]) -> int:
    v = sorted(values)
    if not v:
        return 0
    mid = len(v) // 2
    return v[mid] if len(v) % 2 else rdiv(v[mid - 1] + v[mid], 2)


def score(questions: list[dict], answers: dict[int, int]) -> int:
    """How many answers are right; ``answers`` maps a question id to the chosen original option index."""
    return sum(1 for q in questions if answers.get(q["id"]) == q["correct"])


def finals(attempts: list[dict]) -> dict[int, dict]:
    """Each student's last submitted attempt."""
    out: dict[int, dict] = {}
    for a in sorted((a for a in attempts if a["submitted_at"] is not None), key=lambda a: (a["submitted_at"], a["id"])):
        out[a["user"]] = a
    return out


def table(people: list[dict], attempts: list[dict], total: int) -> dict:
    """The results table: one row per student who got the test, and the group's numbers."""
    last = finals(attempts)
    open_ = {a["user"]: a for a in attempts if a["submitted_at"] is None}
    rows = []
    for p in people:
        a = last.get(p["id"])
        if a is not None:
            pc = pct(a["score"], total)
            rows.append({"user": p["id"], "name": p["name"], "status": "done", "score": a["score"], "total": total, "pct": pc, "grade": grade(pc),
                         "seconds": max(0, (a["submitted_at"] - a["started_at"]) // 1000), "at": a["submitted_at"], "auto": bool(a.get("auto"))})
        elif p["id"] in open_:
            rows.append({"user": p["id"], "name": p["name"], "status": "working", "score": None, "total": total, "pct": None, "grade": None,
                         "seconds": None, "at": open_[p["id"]]["started_at"], "answered": open_[p["id"]].get("answered", 0)})
        else:
            rows.append({"user": p["id"], "name": p["name"], "status": "waiting", "score": None, "total": total, "pct": None, "grade": None,
                         "seconds": None, "at": None})
    done = [r for r in rows if r["status"] == "done"]
    pcs = [r["pct"] for r in done]
    dist = {g: sum(1 for r in done if r["grade"] == g) for g in (5, 4, 3, 2)}
    stats = {"people": len(rows), "done": len(done), "working": sum(1 for r in rows if r["status"] == "working"),
             "waiting": sum(1 for r in rows if r["status"] == "waiting"), "avg": rdiv(sum(pcs), len(pcs)) if pcs else 0, "median": median(pcs),
             "avg_score_x10": rdiv(10 * sum(r["score"] for r in done), len(done)) if done else 0, "grades": dist}
    rows.sort(key=lambda r: ({"done": 0, "working": 1, "waiting": 2}[r["status"]], -(r["pct"] or 0), r["seconds"] or 0, r["name"], r["user"]))
    return {"rows": rows, "stats": stats}


def _ranked(last: dict[int, dict]) -> list[dict]:
    return sorted(last.values(), key=lambda a: (-a["score"], a["submitted_at"] - a["started_at"], a["user"]))


def questions_report(questions: list[dict], attempts: list[dict]) -> dict:
    """Per question: % correct, discrimination, how often each option was picked, and a flag with advice."""
    last = finals(attempts)
    ranked = _ranked(last)
    n = len(ranked)
    k = max(1, rdiv(27 * n, 100)) if n >= MIN_FLAGS else 0
    top, bottom = ranked[:k], ranked[n - k:] if k else []
    out = []
    for pos, q in enumerate(questions):
        picks = [0, 0, 0, 0]
        blank = 0
        for a in ranked:
            c = a["answers"].get(q["id"])
            if c is None:
                blank += 1
            else:
                picks[c] += 1
        right = picks[q["correct"]]
        p = pct(right, n)
        tp = pct(sum(1 for a in top if a["answers"].get(q["id"]) == q["correct"]), k) if k else None
        bp = pct(sum(1 for a in bottom if a["answers"].get(q["id"]) == q["correct"]), k) if k else None
        disc = tp - bp if k else None
        wrong = [i for i in range(4) if i != q["correct"]]
        lead = max(wrong, key=lambda i: (picks[i], -i))
        flag, pick = None, None
        if n >= MIN_FLAGS:
            if tp < 50 and disc <= 10:
                flag = "key"
            elif p < 50:
                flag = "hard"
            elif p >= 90:
                flag = "easy"
            if flag in ("key", "hard") and pct(picks[lead], n) >= 30:
                pick = {"option": lead, "letter": LETTERS[lead], "pct": pct(picks[lead], n)}
        out.append({"id": q["id"], "pos": pos + 1, "topic": q["topic"], "right": right, "n": n, "pct": p, "top": tp, "bottom": bp, "disc": disc,
                    "picks": [pct(x, n) for x in picks], "counts": picks, "blank": blank, "flag": flag, "pick": pick})
    return {"n": n, "k": k, "questions": out}


def topics_report(questions: list[dict], attempts: list[dict]) -> list[dict]:
    """Per topic (in the order the topics first appear): the group's % correct and each student's."""
    last = finals(attempts)
    order: list[str] = []
    for q in questions:
        if q["topic"] not in order:
            order.append(q["topic"])
    out = []
    for topic in order:
        qs = [q for q in questions if q["topic"] == topic]
        right = sum(1 for a in last.values() for q in qs if a["answers"].get(q["id"]) == q["correct"])
        whole = len(qs) * len(last)
        people = {u: pct(sum(1 for q in qs if a["answers"].get(q["id"]) == q["correct"]), len(qs)) for u, a in sorted(last.items())}
        out.append({"topic": topic, "questions": [questions.index(q) + 1 for q in qs], "pct": pct(right, whole), "people": people})
    return out


def retest_plan(questions: list[dict], attempts: list[dict], limit: int = 2) -> dict:
    """The most-missed topics (below 60 %, at most two), their often-missed questions (below 70 %; a question whose
    key is in doubt is left out) and the students who got at least one of them wrong."""
    rep = questions_report(questions, attempts)
    by_id = {r["id"]: r for r in rep["questions"]}
    weak = sorted((t for t in topics_report(questions, attempts) if t["pct"] < 60), key=lambda t: (t["pct"], t["questions"][0]))[:limit]
    names = [t["topic"] for t in weak]
    keep = [q for q in questions if q["topic"] in names and by_id[q["id"]]["pct"] < 70 and by_id[q["id"]]["flag"] != "key"]
    skipped = [by_id[q["id"]]["pos"] for q in questions if q["topic"] in names and by_id[q["id"]]["flag"] == "key"]
    last = finals(attempts)
    missed = sorted(u for u, a in last.items() if any(a["answers"].get(q["id"]) != q["correct"] for q in keep))
    return {"topics": names, "questions": [q["id"] for q in keep], "skipped": skipped, "students": missed,
            "before": pct(sum(1 for a in last.values() for q in questions if q["topic"] in names and a["answers"].get(q["id"]) == q["correct"]),
                          sum(1 for _ in last.values() for q in questions if q["topic"] in names))}


def progress(questions: list[dict], attempts: list[dict], topics: list[str], re_questions: list[dict], re_attempts: list[dict]) -> dict:
    """The group's % on ``topics`` before and after the retest: a student who took the retest counts with the retest,
    everyone else with their first result."""
    first, again = finals(attempts), finals(re_attempts)
    qa = [q for q in questions if q["topic"] in topics]
    qb = [q for q in re_questions if q["topic"] in topics]
    right_a = sum(1 for a in first.values() for q in qa if a["answers"].get(q["id"]) == q["correct"])
    right_b = whole_b = 0
    for u, a in first.items():
        if u in again and qb:
            right_b += sum(1 for q in qb if again[u]["answers"].get(q["id"]) == q["correct"])
            whole_b += len(qb)
        else:
            right_b += sum(1 for q in qa if a["answers"].get(q["id"]) == q["correct"])
            whole_b += len(qa)
    return {"before": pct(right_a, len(qa) * len(first)), "after": pct(right_b, whole_b), "retook": sum(1 for u in first if u in again)}
