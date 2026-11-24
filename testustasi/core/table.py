"""The results table as a CSV file that opens correctly in Excel (the JS port is shared/table.js): UTF-8 with a BOM, a
``;`` separator (Excel in Uzbek and Russian locales expects it), CRLF line ends, quoted fields, and no cell starting with
``= + - @`` (a name like "=HYPERLINK(...)" stays text)."""

from __future__ import annotations

BOM = "\ufeff"


def mmss(seconds: int | None) -> str:
    if seconds is None:
        return ""
    return f"{seconds // 60}:{seconds % 60:02d}"


def cell(value: object) -> str:
    s = "" if value is None else str(value)
    if s[:1] in ("=", "+", "-", "@", "\t", "\r"):
        s = "'" + s
    if any(ch in s for ch in ';"\n\r'):
        s = '"' + s.replace('"', '""') + '"'
    return s


def csv_text(labels: dict[str, str], rows: list[dict], marks: dict[int, list[int | None]], total: int, stamp) -> str:
    """``labels``: column titles and status words in the teacher's language (the score as a plain number: "7/10" would
    become a date in Excel); ``marks[user]`` is 1/0/None per question
    (right, wrong, no answer); ``stamp(ms)`` formats a time."""
    head = [labels["no"], labels["name"], labels["score"], labels["pct"], labels["grade"], labels["time"], labels["status"], labels["at"]]
    head += [f"{i}" for i in range(1, total + 1)]
    lines = [";".join(cell(h) for h in head)]
    for i, r in enumerate(rows, 1):
        done = r["status"] == "done"
        row = [i, r["name"], r["score"] if done else "", r["pct"] if done else "", r["grade"] if done else "", mmss(r["seconds"]) if done else "",
               labels[f"st_{r['status']}"], stamp(r["at"]) if done and r["at"] else ""]
        row += ["" if m is None else m for m in marks.get(r["user"], [None] * total)] if done else [""] * total
        lines.append(";".join(cell(v) for v in row))
    return BOM + "\r\n".join(lines) + "\r\n"
