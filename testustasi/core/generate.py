"""The rule-based question generator (the JS port is shared/generate.js): a pure function from a text to multiple-choice
questions, used when no AI key is set, in the browser demo and in the "O'zingiz sinab ko'ring" box.

Four kinds, every one backed by the sentence it came from (the quote):

* ``def`` — a definition asked by its meaning: "Barg sirtidagi mayda teshikchalar nima deb ataladi?";
* ``rev`` — a term asked for its definition: "Xloroplast deb nimaga aytiladi?" (the options are the text's definitions);
* ``num`` — a year, a percentage or a count: "Fotosintez necha bosqichda boradi?";
* ``gap`` — a key term hidden in an important sentence, the options in the same grammatical form.

The distractors are always other terms (or numbers) of the same text, of the same kind where possible. Quality over
quantity: a sentence that starts with "Bu"/"U" (it needs the previous one), a condition ("… bo'lmasa, …" where other
options could be true too), the text's own title as the hidden word, a plural gap and anything without three good
distractors are skipped — the generator returns fewer questions rather than bad ones."""

from __future__ import annotations

from .numq import question as num_question
from .passages import canonical, split, title_of
from .terms import PRONOUN_START, definitions, key_terms, topics
from .text import WORD, cap, h32, low, norm_match
from .uzwords import inflect, stem

LEVEL = {"def": 1, "rev": 2, "num": 2, "gap": 3}
ORDERS = {"easy": ("def", "num", "rev", "gap"), "hard": ("gap", "rev", "num", "def"), "mixed": ("def", "gap", "num", "rev")}
# How much of each kind a mix wants (relative): the next question is the kind furthest below its share.
WEIGHTS = {"easy": {"def": 5, "num": 3, "rev": 2, "gap": 1}, "hard": {"gap": 5, "rev": 3, "num": 2, "def": 1},
           "mixed": {"def": 4, "gap": 4, "num": 2, "rev": 2}}
SAFE = ("", "ni", "ning", "ga", "ka", "qa", "da", "dan")  # case endings an option can take as well
PROCESS = {"jarayon", "hodisa", "harakat", "usul", "qaytish"}
MIXES = tuple(ORDERS)
COUNTS = (5, 10, 15, 20)


def analyse(text: str, title: str = "") -> dict:
    ps = split(text)
    defs = definitions(ps)
    terms = key_terms(ps, defs)
    name = title or title_of(ps, "")
    return {"passages": ps, "defs": defs, "terms": terms, "topics": topics(ps, defs, terms, name), "title": name, "body": canonical(ps)}


def _stems(text: str) -> list[str]:
    return [stem(w) for w in WORD.findall(text)]


def _related(a: dict, b: dict) -> bool:
    """One term inside the other ("barg" and "barg plastinkasi", "tovush" and "ultratovush"); "barg bandi" and
    "barg plastinkasi" are not related: they are the best distractors for each other."""
    wa, wb = a["key"].split(" "), b["key"].split(" ")
    if set(wa) <= set(wb) or set(wb) <= set(wa):
        return True
    return any(len(x) >= 4 and len(y) >= 4 and x != y and (x in y or y in x) for x in wa for y in wb)


def _distractors(answer: dict, terms: list[dict], context: str, seed: str) -> list[dict] | None:
    """Three other terms of the text, the same kind first; never one the question itself names."""
    seen = set(_stems(context))
    ranked = []
    for k in terms:
        if k["key"] == answer["key"] or _related(k, answer) or all(w in seen for w in k["key"].split(" ")):
            continue
        same = 0 if answer["cls"] and k["cls"] == answer["cls"] else 2 if (k["cls"] in PROCESS) != (answer["cls"] in PROCESS) else 1
        group = 2 if k["kind"] == "minor" else 0 if (k["kind"] == "def") == (answer["kind"] == "def") else 1
        ranked.append(((same, group, abs(len(k["text"]) - len(answer["text"])) // 10, h32(f"{seed}|{k['key']}")), k))
    ranked.sort(key=lambda x: x[0])
    return [k for _, k in ranked[:3]] if len(ranked) >= 3 else None


def _q(kind: str, p: int, s: int, stem_q: str, answer: str, others: list[str], expl: str, quote: str, key: str, topic: str) -> dict | None:
    opts = [cap(x) for x in others]
    if len({norm_match(x) for x in [answer, *opts]}) < 4:
        return None
    pos = h32(f"{kind}|{stem_q}") % 4
    opts.insert(pos, cap(answer))
    return {"kind": kind, "passage": p, "sent": s, "uid": f"{kind}:{p}:{s}", "key": key, "level": LEVEL[kind], "topic": topic,
            "stem": stem_q, "options": opts, "correct": pos, "explanation": expl, "quote": quote}


def _usable(s: str) -> bool:
    ws = WORD.findall(s)
    return 25 <= len(s) <= 220 and not s.endswith("?") and len(ws) >= 4 and low(ws[0]) not in PRONOUN_START


def _gap(s: str, p: int, si: int, a: dict, title_keys: set[str]) -> dict | None:
    if "bo'lmasa" in s or "agar " in low(s) or "sa, " in s:
        return None
    toks = list(WORD.finditer(s))
    st = [stem(m.group()) for m in toks]
    for t in a["terms"]:
        ks = t["key"].split(" ")
        if t["kind"] == "minor" or all(k in title_keys for k in ks):
            continue
        for j in range(len(st) - len(ks) + 1):
            if st[j:j + len(ks)] != ks:
                continue
            last, base = low(toks[j + len(ks) - 1].group()), low(t["text"].split(" ")[-1])
            if not last.startswith(base) or last[len(base):] not in (SAFE if t["kind"] in ("def", "pair") else ("", "ni")):
                break  # a plain word is hidden only as a subject or an object ("____ ajraladi"), never as a place ("____da")
            suf = last[len(base):]
            start, end = toks[j].start(), toks[j + len(ks) - 1].end()
            gapped = s[:start] + "____" + s[end:]
            ds = _distractors(t, a["terms"], gapped, s)
            if ds is None:
                break
            stem_q = f"Bo'sh joyga mos javobni tanlang: «{gapped}»"
            return _q("gap", p, si, stem_q, inflect(t["text"], suf), [inflect(x["text"], suf) for x in ds],
                      "Gap matnda aynan shunday berilgan.", s, t["key"], a["topics"][p])
    return None


def candidates(a: dict) -> list[dict]:
    """Every question the rules can make from an analysed text, in reading order."""
    out: list[dict] = []
    sentences = [s for p in a["passages"] for s in p["sentences"]]
    by_key = {t["key"]: t for t in a["terms"]}
    for d in a["defs"]:
        t, topic = by_key[d["key"]], a["topics"][d["p"]]
        verb = "nima deyiladi" if d["form"] == "called" else "nima deb aytiladi" if d["form"] == "said" else "nima deb ataladi"
        stem_q = f"{cap(d['def'])}{d['suf']} {verb}?"
        ds = _distractors(t, a["terms"], stem_q, stem_q)
        if ds:
            q = _q("def", d["p"], d["s"], stem_q, t["text"], [x["text"] for x in ds], f"{cap(d['def'])} — bu {t['text']}.", d["sentence"], t["key"], topic)
            if q:
                out.append(q)
        own = set(d["key"].split(" "))
        others = [x for x in a["defs"] if x["key"] != d["key"] and len(x["def"]) <= 110 and not own & set(_stems(x["def"]))
                  and not _related(by_key[x["key"]], t)]
        others.sort(key=lambda x: (0 if x["cls"] == d["cls"] else 1, abs(len(x["def"]) - len(d["def"])) // 8, h32(f"rev|{d['key']}|{x['key']}")))
        if len(d["def"]) <= 110 and len(others) >= 3:
            q = _q("rev", d["p"], d["s"], f"{cap(t['text'])} deb nimaga aytiladi?", d["def"], [x["def"] for x in others[:3]],
                   f"{cap(t['text'])} — {d['def']}.", d["sentence"], t["key"], topic)
            if q:
                out.append(q)
    defined = {(d["p"], d["s"]) for d in a["defs"]}
    title_keys = set(_stems(a["title"]))
    for p in a["passages"]:
        for si, s in enumerate(p["sentences"]):
            if (p["n"], si) in defined or not _usable(s):
                continue
            nq = num_question(s, sentences)
            if nq:
                q = _q("num", p["n"], si, nq["stem"], nq["answer"], nq["distractors"], f"Matnga ko'ra: {nq['answer']}.", s, f"num:{p['n']}:{si}", a["topics"][p["n"]])
                if q:
                    out.append(q)
            g = _gap(s, p["n"], si, a, title_keys)
            if g:
                out.append(g)
    out.sort(key=lambda q: (q["passage"], q["sent"], q["uid"]))
    return out


def select(cands: list[dict], n: int, mix: str = "mixed", used: list[dict] = ()) -> list[dict]:
    """Up to ``n`` questions spread over the passages (one per passage per round), one per sentence and one per answer,
    the kinds ordered by ``mix``; ``used`` questions (already in a test) are never repeated."""
    order = ORDERS.get(mix, ORDERS["mixed"])
    weight = WEIGHTS.get(mix, WEIGHTS["mixed"])
    by_p: dict[int, list[dict]] = {}
    for c in cands:
        by_p.setdefault(c["passage"], []).append(c)
    keys = {u["key"] for u in used}
    sents = {(u["passage"], u["sent"]) for u in used}
    uids = {u["uid"] for u in used}
    chosen: list[dict] = []
    count = dict.fromkeys(order, 0)
    moved = True
    while len(chosen) < n and moved:
        moved = False
        for p in sorted(by_p):
            if len(chosen) >= n:
                break
            free = [c for c in by_p[p] if c["uid"] not in uids and c["key"] not in keys and (c["passage"], c["sent"]) not in sents]
            if free:
                c = min(free, key=lambda c: ((count[c["kind"]] + 1) * 60 // weight[c["kind"]], order.index(c["kind"]), c["sent"], c["uid"]))
                count[c["kind"]] += 1
                chosen.append(c)
                keys.add(c["key"])
                sents.add((c["passage"], c["sent"]))
                uids.add(c["uid"])
                moved = True
    chosen.sort(key=lambda q: (q["passage"], q["sent"], q["uid"]))
    return chosen


def generate(text: str, n: int = 10, mix: str = "mixed", title: str = "") -> list[dict]:
    return select(candidates(analyse(text, title)), n, mix)
