"""SQLite storage (aiosqlite, WAL). Parameterised SQL only. Times are UTC milliseconds.

Rules that must never break are in the schema too: one role per person, one open attempt per student and test, one
answer per question in an attempt, an option index 0..3, a summary or a reminder sent once (``sent``). Every row a
teacher owns carries the teacher's id, and every query that reads it is scoped by it."""

from __future__ import annotations

import asyncio
import sqlite3
from contextlib import asynccontextmanager
from pathlib import Path

import aiosqlite

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
  id INTEGER PRIMARY KEY, name TEXT NOT NULL, lang TEXT NOT NULL DEFAULT 'uz' CHECK (lang IN ('uz', 'ru')),
  role TEXT CHECK (role IN ('teacher', 'student')), created_at INTEGER NOT NULL, pend TEXT
);
CREATE TABLE IF NOT EXISTS classes (
  id INTEGER PRIMARY KEY AUTOINCREMENT, teacher INTEGER NOT NULL, name TEXT NOT NULL, created_at INTEGER NOT NULL, UNIQUE (teacher, name)
);
CREATE TABLE IF NOT EXISTS members (grp INTEGER NOT NULL, user INTEGER NOT NULL, joined_at INTEGER NOT NULL, PRIMARY KEY (grp, user));
CREATE INDEX IF NOT EXISTS members_user ON members(user);
CREATE TABLE IF NOT EXISTS sources (
  id INTEGER PRIMARY KEY AUTOINCREMENT, teacher INTEGER NOT NULL, title TEXT NOT NULL, body TEXT NOT NULL,
  kind TEXT NOT NULL CHECK (kind IN ('text', 'pdf', 'docx', 'txt', 'seed')), created_at INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS tests (
  id INTEGER PRIMARY KEY AUTOINCREMENT, teacher INTEGER NOT NULL, source INTEGER NOT NULL, grp INTEGER, title TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'draft' CHECK (status IN ('draft', 'published')), code TEXT UNIQUE,
  minutes INTEGER NOT NULL DEFAULT 15 CHECK (minutes BETWEEN 1 AND 180), attempts INTEGER NOT NULL DEFAULT 1 CHECK (attempts BETWEEN 1 AND 5),
  shuffle INTEGER NOT NULL DEFAULT 1 CHECK (shuffle IN (0, 1)), reveal INTEGER NOT NULL DEFAULT 1 CHECK (reveal IN (0, 1)),
  rank INTEGER NOT NULL DEFAULT 0 CHECK (rank IN (0, 1)), deadline INTEGER, mix TEXT NOT NULL DEFAULT 'mixed', asked INTEGER NOT NULL DEFAULT 10,
  origin TEXT NOT NULL DEFAULT 'rule' CHECK (origin IN ('rule', 'ai', 'mixed')), parent INTEGER, note TEXT, created_at INTEGER NOT NULL, published_at INTEGER
);
CREATE INDEX IF NOT EXISTS tests_teacher ON tests(teacher, status);
CREATE TABLE IF NOT EXISTS questions (
  id INTEGER PRIMARY KEY AUTOINCREMENT, test INTEGER NOT NULL, pos INTEGER NOT NULL, kind TEXT NOT NULL, uid TEXT NOT NULL, key TEXT NOT NULL,
  passage INTEGER NOT NULL, sent INTEGER NOT NULL, level INTEGER NOT NULL CHECK (level BETWEEN 1 AND 3), topic TEXT NOT NULL, stem TEXT NOT NULL,
  options TEXT NOT NULL, correct INTEGER NOT NULL CHECK (correct BETWEEN 0 AND 3), explanation TEXT NOT NULL, quote TEXT NOT NULL,
  edited INTEGER NOT NULL DEFAULT 0 CHECK (edited IN (0, 1))
);
CREATE INDEX IF NOT EXISTS questions_test ON questions(test, pos);
CREATE TABLE IF NOT EXISTS targets (test INTEGER NOT NULL, user INTEGER NOT NULL, PRIMARY KEY (test, user));
CREATE INDEX IF NOT EXISTS targets_user ON targets(user);
CREATE TABLE IF NOT EXISTS attempts (
  id INTEGER PRIMARY KEY AUTOINCREMENT, test INTEGER NOT NULL, user INTEGER NOT NULL, no INTEGER NOT NULL CHECK (no >= 1), seed INTEGER NOT NULL,
  started_at INTEGER NOT NULL, deadline_at INTEGER NOT NULL, submitted_at INTEGER, score INTEGER, auto INTEGER NOT NULL DEFAULT 0 CHECK (auto IN (0, 1)),
  UNIQUE (test, user, no)
);
CREATE UNIQUE INDEX IF NOT EXISTS attempts_one_open ON attempts(test, user) WHERE submitted_at IS NULL;
CREATE INDEX IF NOT EXISTS attempts_due ON attempts(deadline_at) WHERE submitted_at IS NULL;
CREATE TABLE IF NOT EXISTS answers (
  attempt INTEGER NOT NULL, question INTEGER NOT NULL, choice INTEGER NOT NULL CHECK (choice BETWEEN 0 AND 3), at INTEGER NOT NULL,
  PRIMARY KEY (attempt, question)
);
CREATE TABLE IF NOT EXISTS usage (teacher INTEGER NOT NULL, day INTEGER NOT NULL, n INTEGER NOT NULL, PRIMARY KEY (teacher, day));
CREATE TABLE IF NOT EXISTS sent (key TEXT PRIMARY KEY, at INTEGER NOT NULL);
"""


class Database:
    def __init__(self, conn: aiosqlite.Connection) -> None:
        self.conn = conn
        self.lock = asyncio.Lock()  # one transaction at a time on this connection

    @classmethod
    async def open(cls, path: str) -> Database:
        if path != ":memory:":
            Path(path).parent.mkdir(parents=True, exist_ok=True)
        conn = await aiosqlite.connect(path, isolation_level=None)  # we issue BEGIN/COMMIT ourselves
        conn.row_factory = aiosqlite.Row
        await conn.execute("PRAGMA journal_mode=WAL")
        await conn.execute("PRAGMA synchronous=NORMAL")
        await conn.execute("PRAGMA busy_timeout=5000")
        await conn.executescript(SCHEMA)
        return cls(conn)

    async def close(self) -> None:
        await self.conn.close()

    @asynccontextmanager
    async def tx(self):
        """``BEGIN IMMEDIATE`` takes the write lock up front: "check the attempt is open, score it, mark it submitted" is
        one step, neither interleaved between coroutines nor between processes."""
        async with self.lock:
            for attempt in range(6):
                try:
                    await self.conn.execute("BEGIN IMMEDIATE")
                    break
                except sqlite3.OperationalError as err:
                    if "locked" not in str(err) or attempt == 5:
                        raise
                    await asyncio.sleep(0.05 * (attempt + 1))
            try:
                yield self.conn
            except BaseException:
                await self.conn.execute("ROLLBACK")
                raise
            await self.conn.execute("COMMIT")

    async def one(self, sql: str, args: tuple = ()) -> dict | None:
        async with self.conn.execute(sql, args) as cur:
            row = await cur.fetchone()
        return dict(row) if row else None

    async def all(self, sql: str, args: tuple = ()) -> list[dict]:
        async with self.conn.execute(sql, args) as cur:
            return [dict(r) for r in await cur.fetchall()]
