"""UzFit AI — ilovaning kirish nuqtasi (polling yoki webhook)."""
from __future__ import annotations

import asyncio
import os

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from app.bot.handlers import build_root_router
from app.bot.middlewares.core import DBSessionMiddleware, UserMiddleware
from app.config import Settings, get_settings
from app.database.session import dispose_engine, get_sessionmaker, init_db
from app.services.ai_service import AIService
from app.services.reminder_service import ReminderService
from app.utils.logging_config import get_logger, setup_logging

logger = get_logger(__name__)


def _log_db_target(database_url: str) -> None:
    """Ma'lumotlar bazasi ulanish manzilini logga yozadi (parolsiz).

    Bu deploy loglarida qaysi host/user/baza ishlatilayotganini ko'rsatadi —
    DATABASE_URL da yashirin xato (ortiqcha bo'shliq, noto'g'ri host) darhol
    ko'rinadi. Parol hech qachon logga tushmaydi.
    """
    try:
        from sqlalchemy.engine import make_url

        u = make_url(database_url)
        logger.info(
            "DB ulanish: driver=%s host=%s port=%s user=%s db=%s (parol maskalangan)",
            u.drivername, u.host, u.port, u.username, u.database,
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning("DATABASE_URL ni tahlil qilib bo'lmadi: %s", type(exc).__name__)


def create_dispatcher(settings: Settings) -> Dispatcher:
    """Dispatcher ni sozlaydi: middlewarelar, routerlar, workflow data."""
    dp = Dispatcher(storage=MemoryStorage())

    sessionmaker = get_sessionmaker()

    # Middlewarelar (outer — har update uchun)
    dp.update.outer_middleware(DBSessionMiddleware(sessionmaker))
    dp.update.outer_middleware(UserMiddleware())

    # Handlerlarga inyeksiya qilinadigan obyektlar
    dp["settings"] = settings
    dp["ai_service"] = AIService(settings)
    dp["sessionmaker"] = sessionmaker

    dp.include_router(build_root_router())
    return dp


async def _run_polling(bot: Bot, dp: Dispatcher, reminders: ReminderService) -> None:
    reminders.start(timezone=get_settings().timezone)
    try:
        await bot.delete_webhook(drop_pending_updates=True)
        logger.info("Polling rejimida ishga tushdi.")
        await dp.start_polling(bot)
    finally:
        reminders.shutdown()


async def _run_webhook(bot: Bot, dp: Dispatcher, settings: Settings, reminders: ReminderService) -> None:
    from aiohttp import web
    from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application

    # WEBHOOK_URL berilmagan bo'lsa, Render bergan RENDER_EXTERNAL_URL dan olamiz
    base_url = settings.webhook_url.strip() or os.environ.get("RENDER_EXTERNAL_URL", "").strip()
    if not base_url:
        raise RuntimeError(
            "RUN_MODE=webhook uchun WEBHOOK_URL (yoki Render'da RENDER_EXTERNAL_URL) kerak."
        )

    reminders.start(timezone=settings.timezone)
    try:
        await bot.set_webhook(
            url=base_url.rstrip("/") + settings.webhook_path,
            secret_token=settings.webhook_secret or None,
            drop_pending_updates=True,
        )
    except Exception as exc:  # noqa: BLE001 — startup diagnostikasi uchun
        logger.error(
            "Webhook o'rnatilmadi [%s]: %s. BOT_TOKEN to'g'riligini (BotFather) va "
            "WEBHOOK_SECRET faqat [A-Za-z0-9_-] belgilardan iboratligini tekshiring.",
            type(exc).__name__, exc,
        )
        raise
    logger.info("Webhook o'rnatildi: %s%s", base_url.rstrip("/"), settings.webhook_path)

    app = web.Application()

    async def _health(request):  # Render health-check / uyg'otish uchun
        return web.Response(text="UzFit AI OK")

    app.router.add_get("/", _health)
    app.router.add_get("/healthz", _health)

    handler = SimpleRequestHandler(
        dispatcher=dp,
        bot=bot,
        secret_token=settings.webhook_secret or None,
    )
    handler.register(app, path=settings.webhook_path)
    setup_application(app, dp, bot=bot)

    # Render/Railway kabi platformalar PORT env beradi — uni ustun qo'yamiz
    port = int(os.environ.get("PORT", settings.webhook_port))
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, host=settings.webhook_host, port=port)
    await site.start()
    logger.info("Webhook serveri: %s:%s", settings.webhook_host, port)
    try:
        await asyncio.Event().wait()  # cheksiz kutish
    finally:
        reminders.shutdown()
        await runner.cleanup()


async def async_main() -> None:
    settings = get_settings()
    setup_logging(settings.log_level)

    if not settings.bot_token:
        raise RuntimeError(
            "BOT_TOKEN topilmadi. .env faylini to'ldiring (.env.example dan nusxa oling)."
        )

    logger.info("UzFit AI ishga tushmoqda...")
    logger.info("AI provayder: %s (yoqilgan: %s)", settings.ai_provider, settings.ai_enabled)

    _log_db_target(settings.database_url)
    try:
        await init_db(settings.database_url)
    except Exception as exc:  # noqa: BLE001 — startup diagnostikasi uchun
        logger.error(
            "Ma'lumotlar bazasiga ulanib bo'lmadi [%s]: %s. "
            "DATABASE_URL (host/user/parol) va baza mintaqasini tekshiring; "
            "parol noto'g'ri bo'lsa — Render'da baza 'Recovery' orqali sbros qiling.",
            type(exc).__name__, exc,
        )
        raise
    logger.info("Ma'lumotlar bazasi tayyor (jadvallar tekshirildi).")

    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = create_dispatcher(settings)
    reminders = ReminderService(bot, get_sessionmaker())

    try:
        if settings.run_mode.lower() == "webhook":
            await _run_webhook(bot, dp, settings, reminders)
        else:
            await _run_polling(bot, dp, reminders)
    finally:
        await bot.session.close()
        await dispose_engine()


def main() -> None:
    try:
        asyncio.run(async_main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("To'xtatildi.")


if __name__ == "__main__":
    main()
