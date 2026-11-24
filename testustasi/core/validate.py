"""Deterministic checks for questions drafted by AI (the JS port is shared/validate.js; the teacher's edits go through
the same field checks).

Nothing the model returns reaches a teacher, let alone a student, unless it passes every rule here: the shape, exactly
four distinct options, exactly one correct answer, sane lengths, a quote that **really occurs in the source** (after
normalising apostrophes, case, punctuation and spacing), and a correct option grounded in that quote. A question that
fails is dropped (and replaced by another one), never shown. The option order is then set by the server, so an
instruction hidden in a PDF like "make every answer A" changes nothing."""

from __future__ import annotations

from .text import WORD, InputError, clean, h32, norm_match
from .uzwords import number_word

LIMITS = {"stem": (8, 300), "option": (1, 120), "explanation": (0, 400), "topic": (2, 40), "quote": (12, 400)}
LEVELS = {"oson": 1, "o'rta": 2, "orta": 2, "qiyin": 3, "easy": 1, "medium": 2, "hard": 3}


class Rejected(ValueError):
    """Why a drafted question was dropped (logged as a count per reason, never shown)."""


def field(value: object, name: str) -> str:
    lo, hi = LIMITS[name]
    if not isinstance(value, str):
        raise Rejected(name)
    s = clean(value, hi + 1)
    if len(s) > hi or len(s) < lo or (lo and sum(ch.isalnum() for ch in s) < 1):
        raise Rejected(name)
    return s


def options(value: object) -> list[str]:
    if not isinstance(value, list) or len(value) != 4:
        raise Rejected("options")
    opts = [field(v, "option") for v in value]
    if len({norm_match(o) for o in opts}) != 4 or any(not norm_match(o) for o in opts):
        raise Rejected("distinct")
    return opts


def correct_index(value: object) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or not 0 <= value <= 3:
        raise Rejected("correct")
    return value


def occurs(quote: str, source_norm: str) -> bool:
    q = norm_match(quote)
    return len(q) >= 12 and f" {q} " in f" {source_norm} "


def grounded(answer: str, quote: str) -> bool:
    """Some word of the correct option (or its number) is in the quote: "Xloroplast" and "… tanachalar xloroplast deb
    ataladi" are grounded, an answer the quote never mentions is not."""
    qwords = norm_match(quote).split(" ")
    spelled = [str(got[0]) for i in range(len(qwords)) if (got := number_word(qwords, i))]  # "ikki bosqich" grounds "2"
    for w in norm_match(answer).split(" "):
        if w.isdigit() and (w in qwords or w in spelled):
            return True
        if len(w) >= 3 and any(q.startswith(w[: max(3, len(w) - 3)]) for q in qwords if len(q) >= 3):
            return True
    return False


def place(opts: list[str], correct: int, stem: str) -> tuple[list[str], int]:
    """The server decides where the correct option stands (from the stem's hash); the others keep their order."""
    pos = h32(f"ai|{stem}") % 4
    rest = [o for i, o in enumerate(opts) if i != correct]
    rest.insert(pos, opts[correct])
    return rest, pos


def passage_of(quote: str, passages: list[dict]) -> int:
    q = norm_match(quote)
    for p in passages:
        if q and q in norm_match(p["text"]):
            return p["n"]
    return 0


def check(raw: object, source_norm: str, passages: list[dict], topics: dict[int, str]) -> dict:
    """One drafted question -> the stored shape (the same as a rule-based one), or Rejected."""
    if not isinstance(raw, dict):
        raise Rejected("shape")
    stem = field(raw.get("stem"), "stem")
    opts = options(raw.get("options"))
    correct = correct_index(raw.get("correct"))
    quote = field(raw.get("quote"), "quote")
    if not occurs(quote, source_norm):
        raise Rejected("quote")
    if not grounded(opts[correct], quote):
        raise Rejected("grounded")
    expl = raw.get("explanation") if isinstance(raw.get("explanation"), str) else ""
    expl = clean(expl, LIMITS["explanation"][1])
    n = passage_of(quote, passages)
    topic = raw.get("topic")
    topic = clean(topic, 40) if isinstance(topic, str) and len(clean(topic, 41)) >= 2 else topics.get(n, "")
    level = LEVELS.get(str(raw.get("difficulty", "")).strip().lower(), 2)
    opts, correct = place(opts, correct, stem)
    return {"kind": "ai", "passage": n, "sent": -1, "uid": f"ai:{h32(norm_match(stem))}", "key": f"ai:{h32(norm_match(opts[correct]))}",
            "level": level, "topic": topic or topics.get(n, ""), "stem": stem, "options": opts, "correct": correct, "explanation": expl, "quote": quote}


def accept(raws: object, source_norm: str, passages: list[dict], topics: dict[int, str], need: int, have: list[dict] = ()) -> tuple[list[dict], dict]:
    """The valid, distinct questions among ``raws`` (at most ``need``) and a count of the rejected ones per reason."""
    out: list[dict] = []
    why: dict[str, int] = {}
    stems = {norm_match(q["stem"]) for q in have}
    for raw in raws if isinstance(raws, list) else []:
        if len(out) >= need:
            break
        try:
            q = check(raw, source_norm, passages, topics)
        except Rejected as err:
            why[str(err)] = why.get(str(err), 0) + 1
            continue
        if norm_match(q["stem"]) in stems:
            why["duplicate"] = why.get("duplicate", 0) + 1
            continue
        stems.add(norm_match(q["stem"]))
        out.append(q)
    return out, why


def edited(data: object, current: dict) -> dict:
    """A teacher's edit of one question: the same field rules (the quote stays the source's)."""
    if not isinstance(data, dict):
        raise InputError("question")
    try:
        stem = field(data.get("stem", current["stem"]), "stem")
        opts = options(data.get("options", current["options"]))
        correct = correct_index(data.get("correct", current["correct"]))
        expl = data.get("explanation", current["explanation"])
        expl = clean(expl, LIMITS["explanation"][1]) if isinstance(expl, str) else ""
        topic = field(data.get("topic", current["topic"]) or current["topic"] or "Mavzu", "topic")
    except Rejected as err:
        raise InputError(f"q_{err}") from err
    return {**current, "stem": stem, "options": opts, "correct": correct, "explanation": expl, "topic": topic}


def words_of(text: str) -> int:
    return len(WORD.findall(text))
