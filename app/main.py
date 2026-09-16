"""UzFit AI — ilovaning kirish nuqtasi (polling yoki webhook)."""
from __future__ import annotations

import asyncio

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

    if not settings.webhook_url:
        raise RuntimeError("RUN_MODE=webhook uchun WEBHOOK_URL majburiy.")

    reminders.start(timezone=settings.timezone)
    await bot.set_webhook(
        url=settings.webhook_url.rstrip("/") + settings.webhook_path,
        secret_token=settings.webhook_secret or None,
        drop_pending_updates=True,
    )
    logger.info("Webhook o'rnatildi: %s", settings.webhook_path)

    app = web.Application()
    handler = SimpleRequestHandler(
        dispatcher=dp,
        bot=bot,
        secret_token=settings.webhook_secret or None,
    )
    handler.register(app, path=settings.webhook_path)
    setup_application(app, dp, bot=bot)

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, host=settings.webhook_host, port=settings.webhook_port)
    await site.start()
    logger.info("Webhook serveri: %s:%s", settings.webhook_host, settings.webhook_port)
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

    await init_db(settings.database_url)

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
