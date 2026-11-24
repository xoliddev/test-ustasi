"""Shared helpers: the texts, the seeded class in a database, a clock the tests can move, the story's people."""

from __future__ import annotations

import json
from contextlib import asynccontextmanager
from functools import cache
from pathlib import Path

from testustasi.core import seedgen
from testustasi.core.clock import at_local, days_from_civil, local_day
from testustasi.db import Database
from testustasi.service import Service

ROOT = Path(__file__).resolve().parent.parent
TEXTS = json.loads((ROOT / "shared" / "data" / "texts.json").read_text(encoding="utf-8"))
TEXT = {t["id"]: t for t in TEXTS}
FOTO = TEXT["fotosintez"]["body"]
TODAY = days_from_civil(2026, 11, 25)
START = at_local(TODAY, 8 * 60)
# Seeded people have negative ids; the tests give the story's two people positive ids so they can sign in.
NODIRA, JASUR = 1, 2
MADINA = -102
OTHER_TEACHER, STRANGER = 8888, 7777
IDS = {-1: NODIRA, -101: JASUR}
SECRET = b"test-only-invite-secret"


@cache
def _world(today: int) -> str:
    return json.dumps(seedgen.world(TEXTS, today))


def world(today: int) -> dict:
    return json.loads(_world(today))


class Clock:
    def __init__(self, start: int = START) -> None:
        self.now = start

    def __call__(self) -> int:
        return self.now

    def skip(self, minutes: float = 0, days: float = 0, seconds: float = 0) -> None:
        self.now += int((minutes * 60 + days * 86_400 + seconds) * 1000)

    def at(self, day: int, minute: int) -> None:
        self.now = at_local(day, minute)


@asynccontextmanager
async def service_env(clock: Clock | None = None, path: str = ":memory:", seed: bool = True, ai=None, ai_per_day: int = 20):
    clock = clock or Clock()
    db = await Database.open(path)
    svc = Service(db, clock=clock, invite_secret=SECRET, ai=ai, ai_per_day=ai_per_day)
    if seed:
        await svc.seed(world(local_day(clock.now)), IDS)
    for uid, name in ((STRANGER, "Begona"), (OTHER_TEACHER, "Aziz ustoz")):
        await svc.touch_user(uid, name, "uz")
    try:
        yield svc, clock
    finally:
        await db.close()


async def foto_draft(svc: Service, n: int = 15, mix: str = "mixed") -> dict:
    src = await svc.add_source(NODIRA, FOTO, "Fotosintez")
    return await svc.make_draft(NODIRA, src["id"], n, mix)


async def published(svc: Service, clock: Clock, minutes: int = 15) -> dict:
    """The story's test: 11 drafted, the 4th ("O'simlik ____ havodan oladi": "kislorodni" is half-true too) deleted."""
    d = await foto_draft(svc)
    d = await svc.delete_question(NODIRA, d["id"], d["questions"][3]["id"])
    await svc.set_settings(NODIRA, d["id"], {"grp": 1, "minutes": minutes, "deadline": clock.now + 2 * 86_400_000})
    view, _ = await svc.publish(NODIRA, d["id"])
    return view
