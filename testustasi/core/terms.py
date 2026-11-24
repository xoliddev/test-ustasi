"""What a text teaches, found by rules (the JS port is shared/terms.js): definitions ("X — Y", "Y X deb ataladi",
"Y-ga X deyiladi", "X deb Y-ga aytiladi"), key terms (defined terms, words and word pairs the text keeps coming back
to) and a short topic for every passage."""

from __future__ import annotations

import re

from .text import WORD, cap, low
from .uzwords import COUNTERS, STOP, case_strip, is_content, stem

PRONOUN_START = {"bu", "u", "ular", "shu", "ushbu", "bunda", "unda", "uning", "ularning", "unga", "undan", "buning", "shuning",
                 "natijada", "shunday", "bular", "o'sha", "uni", "ularni", "biroq", "lekin", "ammo", "chunki", "masalan", "bunga"}
ADJ_END = ("li", "siz", "iy", "viy", "simon", "dosh", "dor", "tik", "chan")
_DASH = re.compile(r"^(?P<term>[^—,;:()«»]{2,60}?) — (?:bu )?(?P<def>[^—]{8,220})\.$")
_NAMED = re.compile(r"^(?P<head>.{8,240}?) deb (?:ham )?ataladi\.$")
_CALLED = re.compile(r"^(?P<head>.{8,240}?) deyiladi\.$")
_SAID = re.compile(r"^(?P<term>[^,;:]{2,60}?) deb (?P<def>.{8,220}?)(?P<suf>ga|ka|qa) aytiladi\.$")
_DIGIT = re.compile(r"[0-9]")


def _ok_term(ws: list[str]) -> bool:
    if not 1 <= len(ws) <= 3 or any(not WORD.fullmatch(w) or _DIGIT.search(w) for w in ws):
        return False
    first, last = low(ws[0]), low(ws[-1])
    return first not in STOP and first not in PRONOUN_START and last not in STOP and len(last) >= 2


def _ok_def(text: str) -> bool:
    ws = WORD.findall(text)
    if len(ws) < 3 or len(text) > 220 or low(ws[0]) in PRONOUN_START:
        return False
    tail = low(ws[-1])
    finite = any(low(w).endswith(("adi", "ydi", "edi")) for w in ws)  # a clause ("… suv bug'lanadi va bu hodisa"), not a noun phrase
    return not finite and not tail.endswith(("di", "gan", "ib", "moqda")) and " bu " not in f" {text} " and ", u " not in text


def _repeated(seq: list[str], body: list[list[str]], skip: int) -> bool:
    """Does the stem sequence occur in a sentence other than ``skip``?"""
    k = len(seq)
    return any(i != skip and any(st[j:j + k] == seq for j in range(len(st) - k + 1)) for i, st in enumerate(body))


def _tail_term(ws: list[str], body: list[list[str]], idx: int) -> int:
    """How many trailing words of "<definition> <term>" are the term ("… qismi barg plastinkasi" -> 2)."""
    k = 1
    while k < 3 and len(ws) - k > 3:
        prev, first = low(ws[-k - 1]), low(ws[-k])
        if prev in STOP or prev in PRONOUN_START or prev.endswith(("lar", "dan", "ning", "ni")) or (prev.endswith(("da", "ga", "ka", "qa")) and stem(prev) != prev):
            break
        izofa = k == 1 and first.endswith("i") and stem(prev) == prev and is_content(prev)
        adjective = prev.endswith(ADJ_END) and not prev.endswith("dagi")
        if izofa or adjective or _repeated([stem(w) for w in ws[-k - 1:]], body, idx):
            k += 1
            continue
        break
    if k < 3 and len(ws) - k > 3 and stem(ws[-1]) in [stem(w) for w in ws[:-k]]:
        k += 1  # "bandi bo'lmagan barglar o'troq barglar": the term qualifies a word of the definition
    return k


def _match(s: str, body: list[list[str]], idx: int) -> tuple[str, str, str, str] | None:
    """(term, definition, case suffix of the definition, form) of a definition sentence, or None."""
    m = _DASH.match(s)
    if m:
        ws = m["term"].split(" ")
        if _ok_term(ws) and _ok_def(m["def"]):
            d = m["def"]
            return m["term"], d[:-3] if d.endswith("dir") and len(d) > 8 else d, "", "dash"
        return None
    m = _SAID.match(s)
    if m:
        return (m["term"], m["def"], m["suf"], "said") if _ok_term(m["term"].split(" ")) and _ok_def(m["def"]) else None
    m = _NAMED.match(s)
    form = "named"
    if not m:
        m, form = _CALLED.match(s), "called"
    if not m:
        return None
    ws = m["head"].split(" ")
    if form == "called":
        cut = max((i for i, w in enumerate(ws[:-1]) if low(w).endswith(("ga", "ka", "qa")) and len(w) > 4), default=-1)
        if cut >= 2 and len(ws) - cut - 1 <= 3:
            term, head = ws[cut + 1:], ws[:cut + 1]
            d = " ".join([*head[:-1], head[-1][:-2]])
            if _ok_term(term) and _ok_def(d):
                return " ".join(term), d, low(ws[cut])[-2:], form
        if "," in m["head"]:
            return None
        # "Bug'ning suyuqlikka aylanishi kondensatsiya deyiladi": no "-ga" before the term, read like "… deb ataladi"
    k = _tail_term(ws, body, idx)
    term, head, suf = ws[-k:], ws[:-k], ""
    d = " ".join(head)
    return (" ".join(term), d, suf, form) if _ok_term(term) and _ok_def(d) else None


def definitions(passages: list[dict]) -> list[dict]:
    """Every definition sentence: {"term", "def", "suf", "form", "p", "s", "sentence", "key", "cls"}; ``cls`` is the
    definition's head word ("jarayon", "modda"), so terms of one kind can be offered as each other's distractors."""
    body = [[stem(w) for w in WORD.findall(s)] for p in passages for s in p["sentences"]]
    out, idx = [], -1
    for p in passages:
        for si, s in enumerate(p["sentences"]):
            idx += 1
            found = _match(s, body, idx)
            if found:
                term, d, suf, form = found
                out.append({"term": term, "def": d, "suf": suf, "form": form, "p": p["n"], "s": si, "sentence": s,
                            "key": " ".join(stem(w) for w in WORD.findall(term)), "cls": stem(WORD.findall(d)[-1])})
    return out


def _display(forms: dict[str, int], lower: bool) -> str:
    """The form to show: the most used form without its case ending ("hujayrasini", "hujayrasida" -> "hujayrasi")."""
    bases: dict[str, int] = {}
    for surface, n in forms.items():
        ws = surface.split(" ")
        base = " ".join([*ws[:-1], case_strip(ws[-1])])
        bases[base] = bases.get(base, 0) + n
    out = sorted(bases.items(), key=lambda kv: (-kv[1], len(kv[0]), kv[0]))[0][0]
    return out.lower() if lower else out


def key_terms(passages: list[dict], defs: list[dict]) -> list[dict]:
    """Defined terms, then word pairs (twice or more) and words (three times or more) the text repeats in at least two
    sentences; words met twice are "minor" (a distractor of last resort, never a hidden word):
    {"key", "text", "kind" ('def' | 'pair' | 'word' | 'minor'), "cls", "n"}."""
    counts: dict[str, dict] = {}
    for p in passages:
        for si, s in enumerate(p["sentences"]):
            ws = WORD.findall(s)
            for j, w in enumerate(ws):
                if not is_content(w):
                    continue
                keys = [(stem(w), w)]
                if j and is_content(ws[j - 1]) and stem(ws[j - 1]) == low(ws[j - 1]):  # "karbonat angidrid", never "barglar parallel"
                    keys.append((f"{stem(ws[j - 1])} {stem(w)}", f"{ws[j - 1]} {w}"))
                for key, surface in keys:
                    c = counts.setdefault(key, {"n": 0, "sents": set(), "forms": {}, "lower": False})
                    c["n"] += 1
                    c["sents"].add((p["n"], si))
                    c["forms"][surface] = c["forms"].get(surface, 0) + 1
                    c["lower"] = c["lower"] or (j > 0 and surface[:1] != surface[:1].upper())
    terms: dict[str, dict] = {}
    for d in defs:
        if d["key"] not in terms:
            text = d["term"]
            if d["form"] in ("dash", "said") and not _is_name(d["key"], counts):
                text = text[:1].lower() + text[1:]
            terms[d["key"]] = {"key": d["key"], "text": text, "kind": "def", "cls": d["cls"], "n": counts.get(d["key"], {"n": 1})["n"]}
    for key in sorted(counts):
        c = counts[key]
        pair = " " in key
        if key in terms or key in COUNTERS or len(c["sents"]) < 2 or c["n"] < 2:
            continue
        kind = "pair" if pair else "word" if c["n"] >= 3 else "minor"
        text = _display(c["forms"], c["lower"])
        if not pair and ((stem(text) != low(text) and not low(text).endswith("lar")) or low(text).endswith(ADJ_END) or all(low(f) == key for f in c["forms"])
                         or (kind == "minor" and any(key in t.split(" ") for t in terms))):
            continue  # "plastinkasi", "atoqli", "parallel" (never inflected: not a noun), the "band" of "barg bandi"
        terms[key] = {"key": key, "text": text, "kind": kind, "cls": "", "n": c["n"]}
    for key in [k for k, t in terms.items() if t["kind"] == "pair"]:
        for part in key.split(" "):  # a word that only lives inside a pair is that pair ("angidrid" -> "karbonat angidrid")
            t = terms.get(part)
            if t and t["kind"] in ("word", "minor") and t["n"] <= terms[key]["n"] + 1:
                del terms[part]
    order = {"def": 0, "pair": 1, "word": 2, "minor": 3}
    return sorted(terms.values(), key=lambda t: (order[t["kind"]], -t["n"], t["key"]))


def _is_name(key: str, counts: dict) -> bool:
    c = counts.get(key)
    return bool(c) and not c["lower"]


def topics(passages: list[dict], defs: list[dict], terms: list[dict], title: str) -> dict[int, str]:
    """A short topic for every passage: its heading, else its first defined term, else its most used key term."""
    out: dict[int, str] = {}
    for p in passages:
        if p["heading"]:
            out[p["n"]] = cap(p["heading"].rstrip("?").strip())[:40]
            continue
        d = next((d for d in defs if d["p"] == p["n"]), None)
        if d:
            out[p["n"]] = cap(d["term"])[:40]
            continue
        stems = [stem(w) for w in WORD.findall(p["text"])]
        best, score = None, 0
        for t in terms:
            n = stems.count(t["key"])
            if n > score:
                best, score = t, n
        out[p["n"]] = cap(best["text"])[:40] if best else (title or "Matn")[:40]
    return out
