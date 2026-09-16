"""Global xatoliklarni boshqarish — foydalanuvchiga stack trace yuborilmaydi."""
from __future__ import annotations

from aiogram import Router
from aiogram.types import ErrorEvent

from app.utils.logging_config import get_logger

logger = get_logger(__name__)
router = Router(name="errors")


@router.error()
async def on_error(event: ErrorEvent) -> bool:
    """Har qanday handler xatosi shu yerga tushadi."""
    logger.exception("Handlerda xatolik: %s", event.exception)

    # Foydalanuvchiga xushmuomala xabar (texnik tafsilotlarsiz)
    update = event.update
    message = None
    if getattr(update, "message", None):
        message = update.message
    elif getattr(update, "callback_query", None) and update.callback_query.message:
        message = update.callback_query.message

    if message is not None:
        try:
            await message.answer(
                "😔 Kechirasiz, kutilmagan xatolik yuz berdi. Biroz keyinroq qayta "
                "urinib ko'ring yoki /start bosing."
            )
        except Exception:
            pass

    # True — xato boshqarildi (aiogram uni qayta ko'tarmaydi)
    return True
