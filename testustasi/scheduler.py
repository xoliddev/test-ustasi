"""Once a minute: close attempts whose time is up, remind students who have not started before a deadline, and send
each teacher's summary once (when everyone has finished — that one also goes out the moment it happens — or when the
deadline passes). Everything is kept in SQLite, so a restart sends nothing twice and misses nothing."""

from __future__ import annotations

import asyncio
import logging

log = logging.getLogger(__name__)


async def tick(service, notifier) -> int:
    return await notifier.send(await service.due_notes())


async def run(service, notifier, every: float = 60.0) -> None:
    while True:
        try:
            await tick(service, notifier)
        except Exception:  # the loop must survive a bad minute
            log.exception("scheduler tick failed")
        await asyncio.sleep(every)
