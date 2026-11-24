"""Tiny PDFs for the tests, written by hand (a text layer in Helvetica, or no text at all like a scanned page)."""

from __future__ import annotations


def _esc(s: str) -> str:
    return s.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def pdf(pages: list[list[str]], encrypt: bool = False) -> bytes:
    objs: list[bytes] = []
    kids = []
    n_pages = len(pages)
    for i, lines in enumerate(pages):
        page_no, content_no = 4 + 2 * i, 5 + 2 * i
        kids.append(f"{page_no} 0 R")
        stream = "BT /F1 11 Tf 50 780 Td 14 TL " + " ".join(f"({_esc(line)}) Tj T*" for line in lines) + " ET" if lines else ""
        objs.append(f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Resources << /Font << /F1 3 0 R >> >> /Contents {content_no} 0 R >>".encode())
        raw = stream.encode("cp1252", "replace")
        objs.append(f"<< /Length {len(raw)} >>\nstream\n".encode() + raw + b"\nendstream")
    head = [b"<< /Type /Catalog /Pages 2 0 R >>", f"<< /Type /Pages /Kids [{' '.join(kids)}] /Count {n_pages} >>".encode(),
            b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>"]
    body = b"%PDF-1.4\n"
    offsets = []
    for k, obj in enumerate(head + objs, 1):
        offsets.append(len(body))
        body += f"{k} 0 obj\n".encode() + obj + b"\nendobj\n"
    xref = len(body)
    body += f"xref\n0 {len(offsets) + 1}\n0000000000 65535 f \n".encode() + b"".join(f"{o:010d} 00000 n \n".encode() for o in offsets)
    extra = " /Encrypt 99 0 R" if encrypt else ""
    body += f"trailer\n<< /Size {len(offsets) + 1} /Root 1 0 R{extra} >>\nstartxref\n{xref}\n%%EOF\n".encode()
    return body


def docx(paragraphs: list[str]) -> bytes:
    import io
    import zipfile

    xml = ('<?xml version="1.0" encoding="UTF-8"?><w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body>'
           + "".join(f"<w:p><w:r><w:t xml:space=\"preserve\">{p.replace('&', '&amp;').replace('<', '&lt;')}</w:t></w:r></w:p>" for p in paragraphs)
           + "</w:body></w:document>")
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr("[Content_Types].xml", "<Types/>")
        z.writestr("word/document.xml", xml)
    return buf.getvalue()
