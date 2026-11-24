"""Run everything in one process: ``python -m testustasi``.

* the Telegram bot (long polling),
* the aiohttp server: the Mini App (/webapp/) and its API,
* the scheduler: expired attempts, reminders before a deadline, the teacher's summary once.
State lives in SQLite, so a restart loses nothing and sends nothing twice.
"""

from __future__ import annotations

import asyncio
import contextlib
import logging
import os

from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.types import MenuButtonWebApp, WebAppInfo
from aiohttp import web

from . import scheduler
from .ai import Gemini
from .base import load
from .bot.notify import Notifier
from .bot.setup import BotConfig, build_dispatcher
from .config import Settings
from .core import seedgen
from .db import Database
from .service import Service
from .web import make_app

log = logging.getLogger("testustasi")


async def main() -> None:
    logging.basicConfig(level=os.environ.get("LOG_LEVEL", "INFO"), format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    logging.getLogger("aiohttp.access").setLevel(logging.WARNING)
    cfg = Settings.from_env()
    db = await Database.open(cfg.db_path)
    ai = Gemini(cfg.gemini_key, cfg.gemini_model, cfg.gemini_timeout) if cfg.gemini_key else None
    service = Service(db, invite_secret=cfg.invite_secret, invite_days=cfg.invite_days, ai=ai, ai_per_day=cfg.ai_per_day, remind_hours=cfg.remind_hours)
    if cfg.seed_demo and await service.seed(seedgen.world(load("texts"), service.today())):
        log.info("seeded the invented class 7-B (three earlier tests)")
    bot = Bot(cfg.bot_token, default=DefaultBotProperties(parse_mode="HTML"))
    me = await bot.get_me()
    bcfg = BotConfig(me.username or "", cfg.webapp_url, cfg.file_max_bytes, cfg.pdf_max_pages, cfg.invite_days)
    dp = build_dispatcher(service, bot, bcfg, cfg.rate_per_minute)
    notifier = Notifier(bot, service, bcfg)
    if cfg.webapp_url:
        await bot.set_chat_menu_button(menu_button=MenuButtonWebApp(text="Test Ustasi", web_app=WebAppInfo(url=cfg.webapp_url)))
    app = make_app(service, cfg.bot_token, notifier, max_age=cfg.initdata_max_age, rate_per_minute=cfg.api_rate_per_minute,
                   bot_username=me.username or "", invite_days=cfg.invite_days)
    runner = web.AppRunner(app)
    await runner.setup()
    await web.TCPSite(runner, cfg.host, cfg.port).start()
    ticker = asyncio.create_task(scheduler.run(service, notifier))
    log.info("Mini App on http://%s:%s/webapp/  bot: @%s  AI drafts: %s", cfg.host, cfg.port, me.username, "on" if ai else "off (rules)")
    try:
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        ticker.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await ticker
        await runner.cleanup()
        await bot.session.close()
        await db.close()


if __name__ == "__main__":
    asyncio.run(main())
