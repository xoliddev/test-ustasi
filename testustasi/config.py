"""Settings from environment variables (see .env.example). Nothing secret has a default, and no secret is ever logged."""

from __future__ import annotations

import hashlib
import hmac
import os
from dataclasses import dataclass
from pathlib import Path


def _load_dotenv(path: Path) -> None:
    """Minimal .env reader so beginners do not need extra packages. Real env vars win."""
    if not path.is_file():
        return
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def _int(name: str, default: int, lo: int, hi: int) -> int:
    raw = os.environ.get(name, str(default)).strip() or str(default)
    if not raw.isdigit() or not lo <= int(raw) <= hi:
        raise SystemExit(f"{name} must be a whole number between {lo} and {hi}, got {raw!r}")
    return int(raw)


def _flag(name: str, default: str) -> bool:
    return os.environ.get(name, default).strip().lower() in ("1", "true", "yes")


@dataclass(frozen=True)
class Settings:
    bot_token: str
    public_url: str = ""
    gemini_key: str = ""
    gemini_model: str = "gemini-2.5-flash"
    gemini_timeout: int = 40
    ai_per_day: int = 20
    file_max_bytes: int = 10_000_000
    pdf_max_pages: int = 30
    invite_secret: bytes = b""
    invite_days: int = 14
    remind_hours: int = 2
    db_path: str = "data/testustasi.db"
    host: str = "0.0.0.0"  # noqa: S104 - the container must listen on all interfaces
    port: int = 8080
    seed_demo: bool = True
    initdata_max_age: int = 3600
    rate_per_minute: int = 30
    api_rate_per_minute: int = 240

    @property
    def webapp_url(self) -> str:
        return f"{self.public_url}/webapp/" if self.public_url else ""

    def __repr__(self) -> str:  # never print the token or the keys
        return f"Settings(public_url={self.public_url!r}, db_path={self.db_path!r}, ai={'on' if self.gemini_key else 'off'})"

    @classmethod
    def from_env(cls, dotenv: Path | None = Path(".env")) -> Settings:
        if dotenv is not None:
            _load_dotenv(dotenv)
        env = os.environ.get
        token = env("BOT_TOKEN", "").strip()
        if not token or ":" not in token or "replace-with" in token:
            raise SystemExit("BOT_TOKEN is missing. Copy .env.example to .env and paste the token from @BotFather.")
        url = env("PUBLIC_URL", "").strip().rstrip("/")
        if url and not url.startswith("https://"):
            raise SystemExit("PUBLIC_URL must start with https:// (Telegram opens Mini Apps only over HTTPS).")
        model = env("GEMINI_MODEL", "").strip() or cls.gemini_model
        if not all(ch.isalnum() or ch in "-._" for ch in model):
            raise SystemExit("GEMINI_MODEL must be a model name like gemini-2.5-flash")
        secret = env("INVITE_SECRET", "").strip().encode()
        if not secret:
            secret = hmac.new(b"testustasi-invites", token.encode(), hashlib.sha256).digest()
        return cls(
            bot_token=token, public_url=url, gemini_key=env("GEMINI_API_KEY", "").strip(), gemini_model=model,
            gemini_timeout=_int("GEMINI_TIMEOUT", cls.gemini_timeout, 5, 180), ai_per_day=_int("AI_PER_DAY", cls.ai_per_day, 0, 1000),
            file_max_bytes=_int("FILE_MAX_BYTES", cls.file_max_bytes, 10_000, 20_000_000), pdf_max_pages=_int("PDF_MAX_PAGES", cls.pdf_max_pages, 1, 300),
            invite_secret=secret, invite_days=_int("INVITE_DAYS", cls.invite_days, 1, 365), remind_hours=_int("REMIND_HOURS", cls.remind_hours, 1, 48),
            db_path=env("DB_PATH", cls.db_path), host=env("HOST", cls.host), port=_int("PORT", cls.port, 1, 65535), seed_demo=_flag("SEED_DEMO", "1"),
            initdata_max_age=_int("INITDATA_MAX_AGE", cls.initdata_max_age, 60, 86_400), rate_per_minute=_int("RATE_PER_MINUTE", cls.rate_per_minute, 1, 1000),
            api_rate_per_minute=_int("API_RATE_PER_MINUTE", cls.api_rate_per_minute, 10, 5000),
        )
