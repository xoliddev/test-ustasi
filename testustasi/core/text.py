"""Text helpers shared by the generator, the quote check and the bot (the JS port is shared/text.js).

Everything here is deterministic and uses only explicit character classes, so Python and JavaScript split, normalise
and hash the very same way: a source text normalised here produces byte-for-byte the same passages, questions and
quotes in the browser."""

from __future__ import annotations

import re
import unicodedata

_BIDI = "".join(f"{chr(a)}-{chr(b)}" for a, b in ((0x200B, 0x200F), (0x202A, 0x202E), (0x2066, 0x2069)))
_CONTROL = re.compile(f"[\x00-\x08\x0b-\x1f\x7f{_BIDI}\ufeff]")
_SPACE = re.compile(r"[ \t\n\r\f\v\u00a0\u2028\u2029\u3000]+")
_HSPACE = re.compile(r"[ \t\f\v\u00a0\u3000]+")
_APOS = re.compile("[\u02bb\u02bc\u2019\u2018`\u00b4\u2032]")
LETTER = "A-Za-zÀ-ɏЀ-ӿ"
WORD = re.compile(f"[{LETTER}0-9](?:[{LETTER}0-9']|-(?=[{LETTER}0-9]))*")
_NOT_WORD = re.compile(f"[^{LETTER}0-9]+")

CYR = {
    "а": "a", "б": "b", "в": "v", "г": "g", "д": "d", "е": "e", "ё": "yo", "ж": "j", "з": "z", "и": "i", "й": "y", "к": "k", "л": "l",
    "м": "m", "н": "n", "о": "o", "п": "p", "р": "r", "с": "s", "т": "t", "у": "u", "ф": "f", "х": "x", "ц": "s", "ч": "ch", "ш": "sh",
    "щ": "sh", "ъ": "'", "ы": "i", "ь": "", "э": "e", "ю": "yu", "я": "ya", "ў": "o'", "қ": "q", "ғ": "g'", "ҳ": "h",
}
_VOWELS = set("аеёиоуэюяўы")


class InputError(ValueError):
    """Bad input; ``code`` maps to an ``err.<code>`` text."""

    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


def clean(text: object, limit: int) -> str:
    """One line: control and bidi characters dropped, spaces squeezed, cut to ``limit`` code points."""
    s = _CONTROL.sub(" ", "" if text is None else str(text))
    return " ".join(p for p in _SPACE.split(s) if p)[:limit]


def normalize_source(text: str) -> str:
    """A pasted or extracted text as it is stored: NFC, one kind of apostrophe, an em dash for a spaced dash, single
    spaces, at most one blank line between paragraphs. Quotes are checked against exactly this text."""
    s = unicodedata.normalize("NFC", text.replace("\r\n", "\n").replace("\r", "\n"))
    s = _APOS.sub("'", _CONTROL.sub(" ", s))
    s = s.replace("\u2013", "—").replace("\u2012", "—").replace(" - ", " — ")
    lines = [_HSPACE.sub(" ", line).strip() for line in s.split("\n")]
    out: list[str] = []
    for line in lines:
        if line or (out and out[-1]):
            out.append(line)
    return "\n".join(out).strip()


def latin(text: str) -> str:
    """Lower-case Uzbek Latin: Cyrillic transliterated ("иккита нон" -> "ikkita non"), every apostrophe-like character
    turned into a plain ``'``."""
    out = []
    prev = " "
    for ch in text.lower():
        if ch == "е" and (not prev.isalpha() or prev in _VOWELS or prev in "ъь"):
            out.append("ye")
        else:
            out.append(CYR.get(ch, ch))
        prev = ch
    return _APOS.sub("'", "".join(out))


def uz_cyrillic(text: str) -> bool:
    """Uzbek written in Cyrillic: more Cyrillic letters than Latin ones, and at least one of ў қ ғ ҳ."""
    cyr = sum(1 for ch in text if "Ѐ" <= ch <= "ӿ")
    lat = sum(1 for ch in text if "a" <= ch.lower() <= "z")
    return cyr > lat and any(ch in text.lower() for ch in "ўқғҳ")


def to_latin(text: str) -> str:
    """Uzbek Cyrillic -> Latin, keeping capitals ("Ўсимлик" -> "O'simlik", "ШАРҚ" -> "ShARQ")."""
    out = []
    prev = " "
    for ch in text:
        lo = ch.lower()
        t = "ye" if lo == "е" and (not prev.isalpha() or prev.lower() in _VOWELS or prev.lower() in "ъь") else CYR.get(lo, ch)
        out.append(t[:1].upper() + t[1:] if ch != lo and lo in CYR else t)
        prev = ch
    return "".join(out)


def norm_match(text: str) -> str:
    """The form used to check that a quote really occurs in the source: Latin, lower case, apostrophes dropped, every
    other non-letter a single space ("O‘simlik  havoni" and "o'simlik havoni," match)."""
    s = latin(unicodedata.normalize("NFC", text)).replace("'", "")
    return " ".join(p for p in _NOT_WORD.split(s) if p)


def words(text: str) -> list[str]:
    return WORD.findall(text)


def low(word: str) -> str:
    return latin(word)


def cap(s: str) -> str:
    return s[:1].upper() + s[1:]


def h32(text: str) -> int:
    """32-bit FNV-1a (the JS port uses Math.imul and gives the same numbers)."""
    h = 0x811C9DC5
    for b in text.encode("utf-8"):
        h ^= b
        h = (h * 0x01000193) & 0xFFFFFFFF
    return h


def rnd(key: str) -> float:
    return h32(key) / 4_294_967_296


def plain_len(text: str) -> int:
    """Length in code points (what a person counts; the JS port uses Array.from)."""
    return len(text)


def short(text: str, limit: int) -> str:
    """Cut at a word boundary with an ellipsis."""
    if len(text) <= limit:
        return text
    cut = text[: limit - 1]
    sp = cut.rfind(" ")
    return (cut[:sp] if sp > limit // 2 else cut).rstrip(" ,;:—") + "…"


def checked_text(value: object, lo: int, hi: int, code: str) -> str:
    """A one-line field (a name, a title, an option): cleaned, at least ``lo`` letters or digits, at most ``hi``."""
    if not isinstance(value, str):
        raise InputError(code)
    s = clean(value, hi + 1)
    if len(s) > hi or sum(ch.isalnum() for ch in s) < lo:
        raise InputError(code)
    return s


def whole(value: object, lo: int, hi: int, code: str) -> int:
    """An int (not a bool, not a float) within [lo, hi]."""
    if not isinstance(value, int) or isinstance(value, bool) or not lo <= value <= hi:
        raise InputError(code)
    return value
