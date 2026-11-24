"""Turn the views' plain rows into Telegram inline keyboards."""

from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo


def markup(rows: list[list[dict]], webapp_url: str = "") -> InlineKeyboardMarkup | None:
    out = []
    for row in rows:
        buttons = []
        for b in row:
            if "url" in b:
                buttons.append(InlineKeyboardButton(text=b["text"], url=b["url"]))
            elif "app" in b:
                if webapp_url:
                    buttons.append(InlineKeyboardButton(text=b["text"], web_app=WebAppInfo(url=webapp_url + b["app"])))
            else:
                buttons.append(InlineKeyboardButton(text=b["text"], callback_data=b["data"]))
        if buttons:
            out.append(buttons)
    return InlineKeyboardMarkup(inline_keyboard=out) if out else None
