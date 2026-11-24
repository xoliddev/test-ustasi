"""Number questions by rule (the JS port is shared/numq.js): a year, a percentage or a count in a sentence becomes
"qaysi yilda", "necha foiz" or "nechta", and the other numbers of the same kind in the text (or close values) are the
distractors. Ranges ("10 dan 20 kungacha"), decades ("1960-yillarda") and "bir" are never asked about."""

from __future__ import annotations

import re

from .text import WORD, cap, low
from .uzwords import COUNTERS, counter_of, number_word

YEAR = re.compile(r"^([0-9]{3,4})-yil(da|dan|i|ga|ning|gi)?$")


def _spans(sentence: str) -> list[tuple[str, int, int]]:
    return [(m.group(), m.start(), m.end()) for m in WORD.finditer(sentence)]


def find(sentence: str) -> dict | None:
    """The first askable number: {"kind" ('year' | 'pct' | 'count'), "value", "start", "end", "ask", "counter"}."""
    sp = _spans(sentence)
    toks = [t for t, _, _ in sp]
    for i, (tok, start, end) in enumerate(sp):
        m = YEAR.match(tok)
        if m:
            return {"kind": "year", "value": int(m[1]), "start": start, "end": end, "ask": f"qaysi yil{m[2] or ''}", "counter": "yil"}
        got = number_word(toks, i)
        if got is None:
            continue
        value, used = got
        last_end = sp[i + used - 1][2]
        nxt = toks[i + used] if i + used < len(toks) else ""
        if value < 2 or low(nxt) in ("dan", "-") or sentence[last_end:last_end + 1] == "-" or (i and low(toks[i - 1]) == "dan"):
            return None
        if i and number_word(toks, i - 1) is not None:
            continue
        if sentence[last_end:last_end + 1] == "%":
            return {"kind": "pct", "value": value, "start": start, "end": last_end + 1, "ask": "necha foiz", "counter": "foiz"}
        if low(tok).endswith("ta") and not tok[:1].isdigit():
            return {"kind": "count", "value": value, "start": start, "end": end, "ask": "nechta", "counter": "ta"}
        if low(nxt) == "ta":
            return {"kind": "count", "value": value, "start": start, "end": sp[i + used][2], "ask": "nechta", "counter": "ta"}
        c = counter_of(nxt) if nxt else None
        if c is None:
            continue
        counter, suf = c
        if suf.endswith("gacha") and " dan " in f" {low(sentence)} ":
            return None
        nstart, nend = sp[i + used][1], sp[i + used][2]
        kind = "pct" if counter == "foiz" else "count"
        return {"kind": kind, "value": value, "start": start, "end": nend, "ask": f"necha {sentence[nstart:nend]}", "counter": counter}
    return None


def label(kind: str, value: int) -> str:
    if kind == "year":
        return f"{value}-yil"
    if kind == "pct":
        return f"{value}%"
    return str(value)


def others(sentences: list[str], kind: str, counter: str, value: int) -> list[int]:
    """Numbers of the same kind elsewhere in the text, closest first."""
    seen: list[int] = []
    for s in sentences:
        f = find(s)
        if f and f["kind"] == kind and (kind != "count" or f["counter"] == counter) and f["value"] != value and f["value"] not in seen:
            seen.append(f["value"])
    return sorted(seen, key=lambda x: (abs(x - value), x))


def near(kind: str, value: int) -> list[int]:
    """Close values when the text has no other numbers of the kind."""
    if kind == "year":
        out = [value + 10, value - 10, value + 100, value - 100, value + 50, value - 50, value + 20, value - 20]
        return [x for x in out if 0 < x <= 2100]
    if kind == "pct":
        out = [value + 10, value - 10, value * 2, (value + 1) // 2, value + 20, value - 5, value + 5]
        return [x for x in out if 1 <= x <= 100]
    if value <= 10:
        out = [value + 1, value - 1, value + 2, value - 2, value + 3, value + 4]
    else:
        out = [value * 2, (value + 1) // 2, value + (value + 1) // 2, value * 3, value + (value + 3) // 4]
    return [x for x in out if x >= 1]


def question(sentence: str, sentences: list[str]) -> dict | None:
    """{"stem", "answer", "distractors"} for a sentence with an askable number, or None."""
    f = find(sentence)
    if f is None:
        return None
    ask = cap(f["ask"]) if f["start"] == 0 else f["ask"]
    stem = (sentence[: f["start"]] + ask + sentence[f["end"]:]).rstrip(" .!") + "?"
    pool: list[int] = []
    for x in others(sentences, f["kind"], f["counter"], f["value"]) + near(f["kind"], f["value"]):
        if x != f["value"] and x not in pool:
            pool.append(x)
    if len(pool) < 3:
        return None
    return {"stem": stem, "answer": label(f["kind"], f["value"]), "distractors": [label(f["kind"], x) for x in pool[:3]], "kind": f["kind"],
            "counter": f["counter"] if f["counter"] in COUNTERS else ""}
