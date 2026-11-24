"""A source text -> numbered passages (the JS port is shared/passages.js).

A teacher's text arrives in many shapes: pasted from Word with blank lines between paragraphs, pasted with single line
breaks, or extracted from a PDF with every line wrapped and words hyphenated at the end of a line. ``split`` turns any
of them into the same structure: headings (short lines without a full stop), paragraphs (wrapped lines joined), and
passages of a readable size, each with its sentences. ``canonical`` writes the passages back as the stored text, so a
quote taken from a passage is always found in the stored source."""

from __future__ import annotations

import re

from .text import WORD, normalize_source, to_latin, uz_cyrillic

MAX_PASSAGE = 900
TARGET_PASSAGE = 650
MIN_PASSAGE = 140
_END = re.compile(r"[.!?…:;»\"')]$")
_ABBR = {"h.k", "mil", "sm", "km", "mm", "kg", "m", "y", "asr", "b", "t", "va h.k", "masalan", "ya'ni", "prof", "dots", "akad"}
_SPLIT = re.compile(r"(?<=[.!?…])[»\"')]?\s+(?=[«\"(A-ZА-ЯЁЎҚҒҲ0-9])")


def is_lower(ch: str) -> bool:
    return ch != ch.upper()


def is_upper(ch: str) -> bool:
    return ch != ch.lower() or "0" <= ch <= "9" or ch in "«\"("


def is_heading(line: str) -> bool:
    """A short line without a full stop at the end: "Fotosintez bosqichlari", "2. Xlorofill", "Fotosintez nima?"."""
    if not line or len(line) > 70 or line[-1] in ".!;:,":
        return False
    n = len(WORD.findall(line))
    return 1 <= n <= 8 and (line[-1] == "?" or not _END.search(line))


def sentences(text: str) -> list[str]:
    """Split a paragraph into sentences; "1771-y.", "va h.k." and "20 sm." do not end a sentence."""
    out: list[str] = []
    buf = ""
    pos = 0
    for m in _SPLIT.finditer(text):
        piece = text[pos:m.start()]
        pos = m.end()
        candidate = (buf + " " + piece).strip() if buf else piece.strip()
        last = WORD.findall(candidate[-8:])
        tail = last[-1].lower() if last else ""
        if tail in _ABBR or (len(tail) == 1 and tail.isalpha()):
            buf = candidate
            continue
        out.append(candidate)
        buf = ""
    rest = text[pos:].strip()
    if rest:
        out.append((buf + " " + rest).strip() if buf else rest)
    elif buf:
        out.append(buf)
    return [s for s in out if s]


def _paragraphs(body: str) -> list[tuple[str | None, str]]:
    """(heading or None, paragraph text) in reading order."""
    items: list[tuple[str | None, str]] = []
    heading: str | None = None
    blocks = body.split("\n\n")
    for bi, block in enumerate(blocks):
        lines = [ln for ln in block.split("\n") if ln]
        para = ""
        for i, line in enumerate(lines):
            nxt = lines[i + 1] if i + 1 < len(lines) else ""
            if not para and is_heading(line) and (nxt or bi < len(blocks) - 1):
                heading = line
                continue
            para = para[:-1] + line if para.endswith("-") and is_lower(line[:1]) else f"{para} {line}".strip()
            if _END.search(line) and nxt and (is_upper(nxt[:1]) or is_heading(nxt)):
                items.append((heading, para))
                para = ""
        if para:
            items.append((heading, para))
    return items


def _chunks(text: str) -> list[str]:
    """A long paragraph cut into pieces of whole sentences."""
    if len(text) <= MAX_PASSAGE:
        return [text]
    out, cur = [], ""
    for s in sentences(text):
        if cur and len(cur) + 1 + len(s) > TARGET_PASSAGE:
            out.append(cur)
            cur = s
        else:
            cur = f"{cur} {s}".strip()
    if cur:
        out.append(cur)
    return out


def split(text: str) -> list[dict]:
    """Numbered passages: {"n", "heading", "text", "sentences"}. Short paragraphs under the same heading are joined."""
    body = normalize_source(text)
    if uz_cyrillic(body):  # the rules read Uzbek Latin: a Cyrillic text is stored (and quoted) in Latin
        body = to_latin(body)
    passages: list[dict] = []
    for heading, para in _paragraphs(body):
        for piece in _chunks(para):
            prev = passages[-1] if passages else None
            if prev and prev["heading"] == heading and (len(prev["text"]) < MIN_PASSAGE or len(piece) < MIN_PASSAGE) \
                    and len(prev["text"]) + len(piece) <= MAX_PASSAGE:
                prev["text"] = f"{prev['text']} {piece}"
                continue
            passages.append({"n": len(passages) + 1, "heading": heading, "text": piece})
    for p in passages:
        p["sentences"] = sentences(p["text"])
    return passages


def canonical(passages: list[dict]) -> str:
    """The stored source: each passage's heading (once) and text, separated by blank lines."""
    out: list[str] = []
    last = None
    for p in passages:
        if p["heading"] and p["heading"] != last:
            out.append(p["heading"])
        last = p["heading"]
        out.append(p["text"])
    return "\n\n".join(out)


def title_of(passages: list[dict], fallback: str = "") -> str:
    first = next((p["heading"] for p in passages if p["heading"]), None)
    return (first or fallback).rstrip("?").strip()
