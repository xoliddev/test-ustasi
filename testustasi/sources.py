"""A teacher's file -> plain text: PDF (pypdf), Word .docx (its XML read directly) or a .txt. The type is decided by
the file's first bytes, never by its name; size, page count and the time spent are limited; a scanned PDF (pictures,
no text layer) is reported honestly so the teacher can paste the text instead."""

from __future__ import annotations

import asyncio
import html
import io
import re
import zipfile

MIN_LETTERS = 100
DOCX_XML_MAX = 8_000_000
_PARA = re.compile(r"</w:p>")
_RUN = re.compile(r"<w:t(?:\s[^>]*)?>([^<]*)</w:t>")
_TAB = re.compile(r"<w:(?:tab|br)\s*/>")


class SourceError(Exception):
    """``code``: file_type, too_big, pages, encrypted, broken, no_text, slow (each has an ``err.<code>`` text)."""

    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


def kind_of(data: bytes) -> str | None:
    if data[:5] == b"%PDF-":
        return "pdf"
    if data[:4] == b"PK\x03\x04":
        return "docx"
    if b"\x00" not in data[:4096]:
        return "txt"
    return None


def _pdf(data: bytes, max_pages: int) -> str:
    from pypdf import PdfReader
    from pypdf.errors import PdfReadError

    try:
        reader = PdfReader(io.BytesIO(data))
        if reader.is_encrypted and not reader.decrypt(""):
            raise SourceError("encrypted")
        if len(reader.pages) > max_pages:
            raise SourceError("pages")
        return "\n\n".join((page.extract_text() or "").strip() for page in reader.pages)
    except SourceError:
        raise
    except (PdfReadError, ValueError, KeyError, TypeError, OSError, RecursionError) as err:
        raise SourceError("broken") from err


def _docx(data: bytes) -> str:
    try:
        with zipfile.ZipFile(io.BytesIO(data)) as z:
            info = z.getinfo("word/document.xml")
            if info.file_size > DOCX_XML_MAX:  # a zip bomb never gets unpacked
                raise SourceError("too_big")
            xml = z.read(info).decode("utf-8", "replace")
    except SourceError:
        raise
    except (KeyError, zipfile.BadZipFile, OSError, ValueError) as err:
        raise SourceError("file_type") from err
    paras = []
    for chunk in _PARA.split(xml):
        line = "".join(html.unescape(t) for t in _RUN.findall(_TAB.sub("<w:t> </w:t>", chunk)))
        paras.append(line.strip())
    return "\n\n".join(p for p in paras if p)


def _txt(data: bytes) -> str:
    for enc in ("utf-8-sig", "cp1251"):
        try:
            return data.decode(enc)
        except UnicodeDecodeError:
            continue
    raise SourceError("file_type")


def extract(data: bytes, max_bytes: int = 10_000_000, max_pages: int = 30) -> tuple[str, str]:
    """(text, kind) or SourceError. The text is raw; the service normalises and checks its length."""
    if len(data) > max_bytes:
        raise SourceError("too_big")
    kind = kind_of(data)
    if kind is None:
        raise SourceError("file_type")
    text = _pdf(data, max_pages) if kind == "pdf" else _docx(data) if kind == "docx" else _txt(data)
    if sum(ch.isalpha() for ch in text) < MIN_LETTERS:
        raise SourceError("no_text")
    return text, kind


async def extract_async(data: bytes, max_bytes: int = 10_000_000, max_pages: int = 30, timeout: float = 25) -> tuple[str, str]:
    """``extract`` off the event loop, with a time limit (a hostile PDF cannot stall the bot)."""
    try:
        return await asyncio.wait_for(asyncio.to_thread(extract, data, max_bytes, max_pages), timeout)
    except TimeoutError as err:
        raise SourceError("slow") from err
