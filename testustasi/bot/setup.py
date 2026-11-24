"""Dispatcher wiring: rate limiting, user registration, error replies and the screen helper."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from aiogram import Bot, Dispatcher
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import ExceptionTypeFilter
from aiogram.types import CallbackQuery, ErrorEvent, Message, TelegramObject, Update

from ..common import Refused
from ..i18n import plain, t
from ..security import RateLimiter
from ..service import Service
from .markup import markup
from .notify import Notifier

log = logging.getLogger(__name__)


@dataclass(frozen=True)
class BotConfig:
    bot_username: str
    webapp_url: str = ""
    file_max_bytes: int = 10_000_000
    pdf_max_pages: int = 30
    invite_days: int = 14
    files_per_minute: int = 4
    codes_per_minute: int = 6


async def show(event: CallbackQuery | Message, screen: tuple, cfg: BotConfig | None = None, new: bool = False) -> None:
    """Show a screen: edit the message behind a button, or send a new message (after a typed text, a file, a button
    under a message that must stay in the chat)."""
    text, rows = screen
    kb = markup(rows, cfg.webapp_url if cfg else "")
    if isinstance(event, CallbackQuery):
        await event.answer()
        if isinstance(event.message, Message) and not new:
            try:
                await event.message.edit_text(text, reply_markup=kb, disable_web_page_preview=True)
                return
            except TelegramBadRequest as err:
                if "not modified" in str(err):
                    return
        await event.bot.send_message(event.from_user.id, text, reply_markup=kb, disable_web_page_preview=True)
    else:
        await event.answer(text, reply_markup=kb, disable_web_page_preview=True)


def build_dispatcher(service: Service, bot: Bot, cfg: BotConfig, rate_per_minute: int = 30) -> Dispatcher:
    from . import handlers

    dp = Dispatcher()
    limiter = RateLimiter(rate_per_minute)
    files = RateLimiter(cfg.files_per_minute)
    notifier = Notifier(bot, service, cfg)

    async def context(handler, event: TelegramObject, data: dict[str, Any]):
        user = data.get("event_from_user")
        if user is None or user.is_bot:
            return None
        inner_cb = event.callback_query if isinstance(event, Update) else None
        inner_msg = event.message if isinstance(event, Update) else None
        if inner_msg is not None and inner_msg.chat.type != "private":
            return None
        doc = inner_msg is not None and inner_msg.document is not None
        if not limiter.allow(user.id) or (doc and not files.allow(user.id)):
            rec = await service.user(user.id)
            lang = (rec or {}).get("lang", "uz")
            if inner_cb is not None:
                await inner_cb.answer(t(lang, "err.rate"))
            elif doc:
                await inner_msg.answer(t(lang, "err.rate"))
            return None
        record = await service.touch_user(user.id, user.first_name or "", user.language_code)
        data.update(me=user.id, lang=record["lang"], role=record["role"], svc=service, notifier=notifier, cfg=cfg, codes=codes)
        return await handler(event, data)

    codes = RateLimiter(cfg.codes_per_minute)  # guessing test codes stays slow
    dp.update.outer_middleware(context)

    async def refused(event: ErrorEvent) -> None:
        err: Refused = event.exception  # type: ignore[assignment]
        upd = event.update
        target = upd.callback_query or upd.message
        if target is None or target.from_user is None:
            return
        rec = await service.user(target.from_user.id)
        lang = (rec or {}).get("lang", "uz")
        text = t(lang, f"err.{err.code}")
        if text == f"err.{err.code}":
            text = t(lang, "err.generic")
        if isinstance(target, CallbackQuery):
            await target.answer(plain(text), show_alert=True)
        else:
            await target.answer(text)

    dp.errors.register(refused, ExceptionTypeFilter(Refused))
    dp.include_routers(handlers.router, handlers.fallback)
    return dp
