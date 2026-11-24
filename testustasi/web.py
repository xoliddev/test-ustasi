"""aiohttp server: the Mini App (/webapp/), its JSON API and the shared files.

Every ``/api/...`` call must carry ``Authorization: tma <initData>``: the HMAC and ``auth_date`` are checked, then
the call runs *as* that Telegram user through the same Service the bot uses, with a per-user rate limit. Teacher-only
data (questions with their answers, results, the analysis) is refused to anyone else by the service itself.

Every page folder is served explicitly (``/webapp/`` -> its index.html: ``add_static`` would answer 403 for a
folder), bodies are capped (16 KB, 128 KB for a pasted text) and every response carries a strict CSP."""

from __future__ import annotations

import json
import logging
from pathlib import Path

from aiohttp import web

from .common import Refused
from .security import AuthError, RateLimiter, validate_init_data
from .service import Service

log = logging.getLogger(__name__)
ME = web.RequestKey("me", int)
ROOT = Path(__file__).resolve().parent.parent
MAX_BODY = 16 * 1024
MAX_TEXT_BODY = 128 * 1024
CSP = ("default-src 'self'; script-src 'self' https://telegram.org; style-src 'self' 'unsafe-inline'; img-src 'self' data:; "
       "connect-src 'self'; frame-ancestors 'self' https://web.telegram.org https://*.telegram.org; "
       "base-uri 'none'; form-action 'none'; object-src 'none'")
HEADERS = {"Content-Security-Policy": CSP, "X-Content-Type-Options": "nosniff", "Referrer-Policy": "no-referrer",
           "Cross-Origin-Opener-Policy": "same-origin", "Permissions-Policy": "geolocation=(), camera=(), microphone=()"}
STATUS = {"forbidden": 403, "not_found": 404, "auth": 401, "rate": 429, "too_big": 413, "no_shop": 403}


async def body(request: web.Request, limit: int = MAX_BODY) -> dict:
    raw = await request.read()
    if len(raw) > limit:
        raise Refused("too_big")
    try:
        data = json.loads(raw or b"{}")
    except (json.JSONDecodeError, UnicodeDecodeError) as err:
        raise Refused("generic") from err
    if not isinstance(data, dict) or len(data) > 8:
        raise Refused("generic")
    return data


def make_app(service: Service, bot_token: str, notifier=None, *, max_age: int = 3600, rate_per_minute: int = 240, bot_username: str = "",
             invite_days: int = 14) -> web.Application:
    from .web_api import add_routes

    users = RateLimiter(rate_per_minute)

    async def guard_api(request: web.Request) -> None:
        header = request.headers.get("Authorization", "")
        if not header.startswith("tma "):
            raise AuthError("missing")
        user = validate_init_data(header[4:], bot_token, max_age, now=service.now() / 1000)
        if not users.allow(user["id"]):
            raise Refused("rate")
        await service.touch_user(user["id"], user["first_name"], user["language_code"])
        request[ME] = user["id"]

    @web.middleware
    async def guard(request: web.Request, handler):
        try:
            if request.path.startswith("/api/"):
                await guard_api(request)
            resp = await handler(request)
        except AuthError:
            resp = web.json_response({"error": "auth"}, status=401)
        except Refused as err:
            resp = web.json_response({"error": err.code}, status=STATUS.get(err.code, 400))
        except (ValueError, KeyError, TypeError):
            resp = web.json_response({"error": "generic"}, status=400)
        resp.headers.update(HEADERS)
        if request.path.startswith("/api/"):
            resp.headers["Cache-Control"] = "no-store"
        return resp

    async def notify(notes: list[dict]) -> None:
        if notifier is not None and notes:
            try:
                await notifier.send(notes)
            except Exception:  # a failed message never fails the action itself
                log.exception("notify failed")

    async def health(_: web.Request) -> web.Response:
        return web.json_response({"ok": True})

    async def page(_: web.Request) -> web.StreamResponse:
        return web.FileResponse(ROOT / "webapp" / "index.html", headers={"Cache-Control": "no-cache"})

    def redirect(to: str):
        async def go(_: web.Request) -> web.Response:
            raise web.HTTPFound(to)

        return go

    async def unknown(_: web.Request) -> web.Response:
        raise Refused("not_found")

    app = web.Application(middlewares=[guard], client_max_size=MAX_TEXT_BODY + 4096)
    r = app.router
    add_routes(r, service, ME, notify, bot_username, invite_days)
    r.add_route("*", "/api/{tail:.*}", unknown)
    r.add_get("/healthz", health)
    r.add_get("/", redirect("/webapp/"))
    r.add_get("/webapp", redirect("/webapp/"))
    r.add_get("/webapp/", page)
    r.add_static("/webapp/", ROOT / "webapp", append_version=False)
    r.add_static("/shared/", ROOT / "shared", append_version=False)
    return app
