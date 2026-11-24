"""Texts and formats shared by the bot, the Mini App and the demo (the JS port is shared/i18n.js): locale templates with
HTML-escaped parameters, dates relative to today, percentages, counts, times, and the analysis flags with their advice.
Every number shown in two places goes through one of these functions, with the same label."""

from __future__ import annotations

import html
import json
import re
from pathlib import Path

from .core.clock import civil, hhmm, local_day, local_minute

LOCALES = Path(__file__).resolve().parent.parent / "shared" / "locales"
CATALOGS = {lang: json.loads((LOCALES / f"{lang}.json").read_text(encoding="utf-8")) for lang in ("uz", "ru")}
_PARAM = re.compile(r"\{(\w+)\}")


class Raw(str):
    """A parameter that is already safe HTML (built from other templates)."""


def esc(s: object) -> str:
    return html.escape(str(s), quote=False)


def norm_lang(code: str | None) -> str:
    return "ru" if (code or "")[:2].lower() == "ru" else "uz"


def t(lang: str, key: str, **params: object) -> str:
    cat = CATALOGS[norm_lang(lang)]
    template = cat.get(key) or CATALOGS["uz"].get(key) or key
    return _PARAM.sub(lambda m: (str(params[m[1]]) if isinstance(params[m[1]], Raw) else esc(params[m[1]])) if m[1] in params else m[0], template)


def plain(text: str) -> str:
    return html.unescape(re.sub(r"<[^>]+>", "", text))


def date_text(lang: str, day: int) -> str:
    _, m, d = civil(day)
    return t(lang, "fmt.day", d=d, month=t(lang, f"month.{m}"))


def when(lang: str, ms: int, now: int) -> str:
    """"bugun, 23:59", "ertaga, 23:59" or "3-dekabr, 23:59" (Tashkent time)."""
    day, time = local_day(ms), hhmm(local_minute(ms))
    today = local_day(now)
    if day == today:
        return t(lang, "fmt.today", time=time)
    if day == today + 1:
        return t(lang, "fmt.tomorrow", time=time)
    return t(lang, "fmt.when", date=date_text(lang, day), time=time)


def num(n: int) -> str:
    """12345 -> "12 345" (a no-break space would be nicer, a plain one survives every font)."""
    return f"{n:,}".replace(",", " ")


def pct(lang: str, n: int) -> str:
    return t(lang, "fmt.pct", n=n)


def questions(lang: str, n: int) -> str:
    return t(lang, "fmt.questions", n=n)


def minutes(lang: str, n: int) -> str:
    return t(lang, "fmt.minutes", n=n)


def students(lang: str, n: int) -> str:
    return t(lang, "fmt.students", n=n)


def mmss(lang: str, seconds: int) -> str:
    return t(lang, "fmt.time", m=seconds // 60, s=f"{seconds % 60:02d}")


def flag_text(lang: str, r: dict) -> str | None:
    """The advice under a question of the analysis, or None (no flag)."""
    if r["flag"] is None:
        return None
    if r["flag"] in ("key", "hard") and r["pick"]:
        return t(lang, f"flag.{r['flag']}_pick", pct=r["pick"]["pct"], letter=r["pick"]["letter"])
    return t(lang, f"flag.{r['flag']}")
