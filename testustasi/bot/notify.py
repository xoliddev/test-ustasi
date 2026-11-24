"""Messages the bot sends on its own (the service's notes: a new test, a retest, a reminder, the teacher's summary),
each in its reader's language. A failed message never fails the action that caused it."""

from __future__ import annotations

import logging

from aiogram import Bot

from . import views
from .markup import markup

log = logging.getLogger(__name__)


class Notifier:
    def __init__(self, bot: Bot, service, cfg) -> None:
        self.bot, self.svc, self.cfg = bot, service, cfg

    async def send(self, notes: list[dict]) -> int:
        sent = 0
        for n in notes:
            if n["to"] <= 0:  # the seeded people cannot receive messages
                continue
            try:
                user = await self.svc.user(n["to"])
                text, rows = views.note((user or {}).get("lang", "uz"), n, self.svc.now())
                await self.bot.send_message(n["to"], text, reply_markup=markup(rows, self.cfg.webapp_url), disable_web_page_preview=True)
                sent += 1
            except Exception:
                log.warning("could not deliver a %s note", n.get("kind"))
        return sent
