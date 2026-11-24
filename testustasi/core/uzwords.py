"""Small Uzbek word knowledge for the rule-based generator (the JS port is shared/uzwords.js): function words, a
suffix stripper good enough to count "barglarda" and "barg" as one word, inflecting an option with the same suffix,
number words and the counter words that make a number askable ("ikki bosqich" -> "necha bosqich")."""

from __future__ import annotations

from .text import low

_STOP = """
va ham bilan uchun esa lekin ammo biroq chunki agar yoki hamda bu shu u ular uning ularning unda undan unga
buni bunda shunday shuning ushbu o'sha bir bitta har hamma barcha deyarli qariyb taxminan asosan faqat juda
eng ko'p kam katta kichik mayda yangi eski boshqa kabi deb emas bor yo'q edi ekan bo'ladi bo'lgan bo'lib
bo'lsa bo'lishi mumkin qiladi qilgan qiladigan hosil orqali tufayli sifatida tomonidan ataladi deyiladi
aytiladi hisoblanadi iborat kerak nima kim qanday qayer qachon nechta necha masalan ya'ni keyin oldin avval
hozir doim ba'zi ko'pincha birinchi ikkinchi uchinchi yil kun oy soat vaqt jarayon modda qism tur narsa holda
ichida ustida ostida bo'yicha bo'ylab qarab qaraganda natijada tarzda yerda ham-da bular shular o'z o'zi biri
biridir sabab sababli bo'lmasa bo'lmagan yaxshi yuqori past ko'proq kamroq oson qiyin asosiy umumiy turli
muhim ayniqsa hatto yana endi so'ng undan-keyin ostidagi ustidagi
"""
STOP = frozenset(_STOP.split())

# Stripped in grammar order, at most one of each: a case ending, then a possessive one, then the plural.
CASES = ("dagi", "ning", "gacha", "dan", "dir", "ni", "ga", "ka", "qa", "da")
POSSESSIVE = ("lari", "si", "i")
ADJ_I = ("li", "iy", "gi", "ki", "qi")  # adjectives, not a possessive "-i"
DA_ROOTS = {"modda", "parda", "soda", "banda", "poda", "sada", "dunyoda", "aslida", "ayniqsa"}  # words that end in "da" by themselves
VERBISH = ("adi", "ydi", "ladi", "gan", "gach", "moqda", "yapti", "maydi", "masdan", "ishdi", "edi", "ibdi", "ganda", "gani",
           "ilgan", "ilib", "ib", "moq", "sin", "ydilar", "dilar")
CAPS = ("ning", "ni", "ga", "ka", "qa", "da", "dan", "dagi", "lar", "larda", "lardan", "larga", "larni", "larning", "dir", "")

UNITS = {"bir": 1, "ikki": 2, "uch": 3, "to'rt": 4, "besh": 5, "olti": 6, "yetti": 7, "sakkiz": 8, "to'qqiz": 9}
TENS = {"o'n": 10, "yigirma": 20, "o'ttiz": 30, "qirq": 40, "ellik": 50, "oltmish": 60, "yetmish": 70, "sakson": 80, "to'qson": 90}
TA = {"ikkita": 2, "uchta": 3, "to'rtta": 4, "beshta": 5, "oltita": 6, "yettita": 7, "sakkizta": 8, "to'qqizta": 9, "o'nta": 10}
_COUNTERS = """
ta xil bosqich marta kun soat yil oy hafta daqiqa minut sekund metr kilometr km kg gramm litr gradus foiz qism
tur juft qavat bo'lim asr nafar dona qator sahifa gers santimetr sm millimetr mm tonna kishi shtat viloyat
qit'a okean sayyora
"""
COUNTERS = frozenset(_COUNTERS.split())


def stem(word: str) -> str:
    """"barglarda" -> "barg", "kisloroddan" -> "kislorod", "hujayralaridagi" -> "hujayra", "plastinka" stays (lower-case
    Latin). Good enough to count the forms of one word together; never shown to anyone."""
    w = low(word)
    for suf in CASES:
        rest = w[: -len(suf)]
        if w.endswith(suf) and len(rest) >= 3 and (suf != "da" or w not in DA_ROOTS) and (suf != "ka" or rest.endswith("k")) and (suf != "qa" or rest.endswith("q")):
            w = rest
            break
    for suf in POSSESSIVE:
        rest = w[: -len(suf)]
        vowel = rest[-1:] in ("a", "e", "i", "o", "u")
        if w.endswith(suf) and len(rest) >= 3 and (suf != "si" or vowel) and (suf != "i" or (not vowel and rest[-1] != "'" and not w.endswith(ADJ_I))):
            w = rest
            break
    if w.endswith("lar") and len(w) >= 5:
        w = w[:-3]
    return w


def case_strip(word: str) -> str:
    """Only the case ending off, the rest kept: "hujayrasini" -> "hujayrasi", "barglarda" -> "barglar" (a form to show)."""
    w = low(word)
    for suf in CASES:
        rest = w[: -len(suf)]
        if w.endswith(suf) and len(rest) >= 3 and (suf != "da" or w not in DA_ROOTS) and (suf != "ka" or rest.endswith("k")) and (suf != "qa" or rest.endswith("q")):
            return word[: len(word) - len(suf)] if len(word) == len(w) else word
    return word


def suffix_of(word: str, base: str) -> str | None:
    """What follows ``base`` in ``word`` ("barglarda", "barg" -> "larda"), or None if the word is not a form of it."""
    w, b = low(word), low(base)
    return w[len(b):] if w.startswith(b) else None


def inflect(base: str, suffix: str) -> str:
    """Put an option into the same form as the answer: ("kislorod", "ga") -> "kislorodga", ("barg", "ka") -> "bargga",
    ("yaproq", "ga") -> "yaproqqa", ("plastinka", "i") -> "plastinkasi"."""
    if not suffix:
        return base
    last = low(base)[-1:]
    if suffix in ("ga", "ka", "qa"):
        suffix = "ka" if last == "k" else "qa" if last == "q" else "ga"
    elif suffix in ("i", "si"):
        suffix = "si" if last in "aeiou" else "i"
    elif suffix.startswith("i") and last in "aeiou":
        suffix = "s" + suffix
    return base + suffix


def is_content(word: str) -> bool:
    """Could be a key term: not a function word, not a verb form, long enough, not a number."""
    w = low(word)
    if len(w) < 4 or w in STOP or stem(w) in STOP or any(ch.isdigit() for ch in w):
        return False
    return not any(w.endswith(e) for e in VERBISH)


def number_word(tokens: list[str], i: int) -> tuple[int, int] | None:
    """A number spelled at ``tokens[i]`` (digits, "ikki", "o'n ikki", "beshta"): (value, how many tokens)."""
    w = low(tokens[i])
    if w.isdigit() and len(w) <= 7:
        n, used = int(w), 1
        # "20 000" written with a space
        while i + used < len(tokens) and len(tokens[i + used]) == 3 and tokens[i + used].isdigit() and n < 1000:
            n, used = n * 1000 + int(tokens[i + used]), used + 1
        return n, used
    if w in TA:
        return TA[w], 1
    if w in TENS:
        if i + 1 < len(tokens) and low(tokens[i + 1]) in UNITS:
            return TENS[w] + UNITS[low(tokens[i + 1])], 2
        return TENS[w], 1
    if w in UNITS:
        return UNITS[w], 1
    return None


def counter_of(word: str) -> tuple[str, str] | None:
    """("bosqichda") -> ("bosqich", "da"); ("foizi") -> ("foiz", "i"); None for an ordinary word."""
    w = low(word)
    for c in sorted(COUNTERS, key=lambda x: (-len(x), x)):
        if w.startswith(c) and (len(w) == len(c) or w[len(c):] in (*CAPS, "i", "si", "ni", "dan", "ga", "gacha", "igacha", "sigacha", "lik", "ligi")):
            return c, w[len(c):]
    return None
