"""A tiny Telegram simulator: real aiogram Dispatcher and handlers, mocked Bot API session.

Every outgoing call (sendMessage, editMessageText, answerCallbackQuery) is recorded, and each user's chat is kept as
a list of messages, so tests can "press" buttons by their visible text like a real person.
"""

from __future__ import annotations

import importlib
import itertools
from datetime import UTC, datetime

from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.client.session.base import BaseSession
from aiogram.methods import AnswerCallbackQuery, DeleteMessage, EditMessageText, GetFile, SendDocument, SendMessage, TelegramMethod
from aiogram.types import Chat, File, Message, Update, User

from testustasi.bot import handlers
from testustasi.bot.notify import Notifier
from testustasi.bot.setup import BotConfig, build_dispatcher
from testustasi.service import Service

BOT_USER = User(id=4242, is_bot=True, first_name="Test Ustasi", username="ustasi_test_bot")


class MockSession(BaseSession):
    def __init__(self) -> None:
        super().__init__()
        self.calls: list[TelegramMethod] = []
        self.ids = itertools.count(1)
        self.chats: dict[int, list[dict]] = {}
        self.latest: dict[int, dict] = {}  # the message a person looks at: last sent or last edited
        self.file = b""  # what "downloading" a document returns
        self.documents: list[tuple[int, bytes, str]] = []

    async def make_request(self, bot: Bot, method: TelegramMethod, timeout: int | None = None):
        self.calls.append(method)
        if isinstance(method, SendMessage):
            mid = next(self.ids)
            msg = {"id": mid, "text": method.text, "markup": method.reply_markup}
            self.chats.setdefault(int(method.chat_id), []).append(msg)
            self.latest[int(method.chat_id)] = msg
            return self._message(int(method.chat_id), mid, method.text)
        if isinstance(method, EditMessageText):
            chat = self.chats.setdefault(int(method.chat_id), [])
            msg = next((m for m in chat if m["id"] == method.message_id), None)
            if msg is None:
                msg = {"id": method.message_id}
                chat.append(msg)
            msg.update(text=method.text, markup=method.reply_markup)
            self.latest[int(method.chat_id)] = msg
            return self._message(int(method.chat_id), method.message_id, method.text)
        if isinstance(method, GetFile):
            return File(file_id=method.file_id, file_unique_id="u-" + method.file_id[:8], file_size=len(self.file), file_path="documents/file_1.pdf")
        if isinstance(method, SendDocument):
            doc = method.document
            self.documents.append((int(method.chat_id), doc.data, doc.filename))
            return self._message(int(method.chat_id), next(self.ids), method.caption or "")
        if isinstance(method, DeleteMessage):
            chat = self.chats.get(int(method.chat_id), [])
            self.chats[int(method.chat_id)] = [m for m in chat if m["id"] != method.message_id]
            return True
        return True

    @staticmethod
    def _message(chat_id: int, mid: int, text: str) -> Message:
        return Message(message_id=mid, date=datetime.now(UTC), chat=Chat(id=chat_id, type="private"), from_user=BOT_USER, text=text)

    async def close(self) -> None:
        return None

    async def stream_content(self, url, headers=None, timeout=30, chunk_size=65536, raise_for_status=True):
        yield self.file


class TgSim:
    def __init__(self, svc: Service, rate: int = 1000, webapp: str = "https://ustasi.example/webapp/", codes: int = 100) -> None:
        self.session = MockSession()
        self.bot = Bot("4242:TEST-ONLY-TOKEN", session=self.session, default=DefaultBotProperties(parse_mode="HTML"))
        self.cfg = BotConfig("ustasi_test_bot", webapp, codes_per_minute=codes, files_per_minute=100)
        importlib.reload(handlers)  # aiogram routers attach to one dispatcher only; tests build many
        self.dp = build_dispatcher(svc, self.bot, self.cfg, rate_per_minute=rate)
        self.notifier = Notifier(self.bot, svc, self.cfg)
        self.svc = svc
        self.updates = itertools.count(1)

    def user(self, uid: int) -> dict:
        return {"id": uid, "is_bot": False, "first_name": "User", "language_code": "uz"}

    async def feed(self, payload: dict) -> None:
        upd = Update.model_validate({"update_id": next(self.updates), **payload}, context={"bot": self.bot})
        await self.dp.feed_update(self.bot, upd)

    async def say(self, uid: int, text: str) -> None:
        extra = {"text": text}
        if text.startswith("/"):
            extra["entities"] = [{"type": "bot_command", "offset": 0, "length": len(text.split()[0])}]
        msg = {"message_id": 10_000 + next(self.updates), "date": int(datetime.now(UTC).timestamp()), "chat": {"id": uid, "type": "private"},
               "from": self.user(uid), **extra}
        await self.feed({"message": msg})

    async def send_file(self, uid: int, data: bytes, name: str = "darslik.pdf") -> None:
        self.session.file = data
        msg = {"message_id": 10_000 + next(self.updates), "date": int(datetime.now(UTC).timestamp()), "chat": {"id": uid, "type": "private"},
               "from": self.user(uid), "document": {"file_id": f"BQACAgIAAxkBAAIB-doc-{uid}", "file_unique_id": "d1", "file_name": name,
                                                    "mime_type": "application/pdf", "file_size": len(data)}}
        await self.feed({"message": msg})

    async def tap_data(self, uid: int, data: str, message_id: int = 1) -> None:
        cq = {"id": str(next(self.updates)), "from": self.user(uid), "chat_instance": "ci", "data": data,
              "message": {"message_id": message_id, "date": int(datetime.now(UTC).timestamp()),
                          "chat": {"id": uid, "type": "private"}, "from": BOT_USER.model_dump(), "text": "…"}}
        await self.feed({"callback_query": cq})

    def find(self, uid: int, label: str):
        for msg in reversed(self.session.chats.get(uid, [])):
            for row in getattr(msg.get("markup"), "inline_keyboard", None) or []:
                for b in row:
                    if label in b.text:
                        return msg, b
        raise AssertionError(f"no button {label!r} for {uid}; last: {self.last(uid)!r}")

    async def tap(self, uid: int, label: str) -> None:
        """Press the newest visible button whose text contains ``label``."""
        msg, b = self.find(uid, label)
        assert b.callback_data, f"{label!r} is a link or the Mini App"
        await self.tap_data(uid, b.callback_data, msg["id"])

    def last(self, uid: int) -> str:
        msg = self.session.latest.get(uid)
        return msg["text"] if msg else ""

    def texts(self, uid: int) -> list[str]:
        return [m["text"] for m in self.session.chats.get(uid, [])]

    def alerts(self) -> list[str]:
        return [c.text for c in self.session.calls if isinstance(c, AnswerCallbackQuery) and c.text]

    def buttons(self, uid: int) -> list[str]:
        msg = self.session.latest.get(uid)
        rows = getattr(msg.get("markup"), "inline_keyboard", None) or [] if msg else []
        return [b.text for row in rows for b in row]

    def apps(self, uid: int) -> list[str]:
        """The Mini App addresses behind the newest message's buttons."""
        msg = self.session.latest.get(uid)
        rows = getattr(msg.get("markup"), "inline_keyboard", None) or [] if msg else []
        return [b.web_app.url for row in rows for b in row if b.web_app]
