"""Vercel serverless webhook entrypoint — UzFit AI.

Telegram bu funksiyaga POST orqali update yuboradi. Har chaqiruv izolyatsiya
qilingan, shuning uchun kerakli obyektlar so'rov ichida quriladi.

⚠️ CHEKLOVLAR (DEPLOY_VERCEL.md ga qarang):
- SQLite serverless da SAQLANMAYDI → DATABASE_URL sifatida Postgres ishlating
  (masalan Neon/Supabase): postgresql+asyncpg://user:pass@host/db
- Ko'p bosqichli oqimlar (ro'yxatdan o'tish, suv/vazn/ovqat kiritish) FSM
  holatini talab qiladi → REDIS_URL (masalan Upstash) o'rnating.
- Reminderlar (APScheduler) bu yerda ISHLAMAYDI — doimiy jarayon yo'q.
"""
from __future__ import annotations

import asyncio
import json
import os
import sys
import traceback
from http.server import BaseHTTPRequestHandler

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import Update
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.bot.handlers import build_root_router
from app.bot.middlewares.core import DBSessionMiddleware, UserMiddleware
from app.config import get_settings
from app.database.models import Base
from app.services.ai_service import AIService

# Warm instance da sxemani takror yaratmaslik uchun bayroq
_schema_ready = False


def _make_storage():
    """REDIS_URL bo'lsa RedisStorage, aks holda MemoryStorage (ogohlantirish bilan)."""
    redis_url = os.environ.get("REDIS_URL", "").strip()
    if redis_url:
        try:
            from aiogram.fsm.storage.redis import RedisStorage

            return RedisStorage.from_url(redis_url)
        except Exception as exc:  # redis paketi yoki ulanish yo'q
            print(f"[webhook] Redis storage yaratilmadi: {exc}", file=sys.stderr)
    else:
        print(
            "[webhook] OGOHLANTIRISH: REDIS_URL yo'q — MemoryStorage ishlatilmoqda. "
            "Serverless da ko'p bosqichli oqimlar (ro'yxatdan o'tish) ishlamasligi mumkin.",
            file=sys.stderr,
        )
    return MemoryStorage()


async def _process(body: bytes) -> None:
    global _schema_ready
    settings = get_settings()

    engine = create_async_engine(settings.database_url, poolclass=NullPool)
    try:
        if not _schema_ready:
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            _schema_ready = True

        sessionmaker = async_sessionmaker(engine, expire_on_commit=False)
        storage = _make_storage()

        bot = Bot(
            token=settings.bot_token,
            default=DefaultBotProperties(parse_mode=ParseMode.HTML),
        )
        dp = Dispatcher(storage=storage)
        dp.update.outer_middleware(DBSessionMiddleware(sessionmaker))
        dp.update.outer_middleware(UserMiddleware())
        dp["settings"] = settings
        dp["ai_service"] = AIService(settings)
        dp["sessionmaker"] = sessionmaker
        dp.include_router(build_root_router())

        update = Update.model_validate(json.loads(body), context={"bot": bot})
        try:
            await dp.feed_update(bot, update)
        finally:
            await bot.session.close()
            close = getattr(storage, "close", None)
            if close is not None:
                try:
                    await close()
                except Exception:
                    pass
    finally:
        await engine.dispose()


class handler(BaseHTTPRequestHandler):
    """Vercel Python runtime kutadigan handler klassi."""

    def _send(self, code: int, text: str) -> None:
        self.send_response(code)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.end_headers()
        self.wfile.write(text.encode("utf-8"))

    def do_POST(self) -> None:  # noqa: N802 (Vercel API talabi)
        settings = get_settings()

        # Webhook maxfiy tokenini tekshiramiz (o'rnatilgan bo'lsa)
        if settings.webhook_secret:
            got = self.headers.get("X-Telegram-Bot-Api-Secret-Token", "")
            if got != settings.webhook_secret:
                self._send(401, "unauthorized")
                return

        length = int(self.headers.get("content-length", 0) or 0)
        body = self.rfile.read(length) if length else b"{}"

        try:
            asyncio.run(_process(body))
            self._send(200, "ok")
        except Exception:
            # Texnik tafsilot faqat ser- loglarga; Telegram ga 200 (retry bo'ronini oldini olish)
            traceback.print_exc()
            self._send(200, "handled")

    def do_GET(self) -> None:  # noqa: N802
        self._send(
            200,
            "UzFit AI webhook tirik. Telegram webhookni shu URL ga o'rnating: "
            "<domen>/api/webhook",
        )
