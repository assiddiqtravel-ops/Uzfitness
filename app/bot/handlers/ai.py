"""AI Murabbiy — savol-javob yordamchisi."""
from __future__ import annotations

from aiogram import F, Router
from aiogram.enums import ChatAction
from aiogram.filters import StateFilter
from aiogram.types import Message

from app.bot.handlers._helpers import get_completed_profile
from app.bot.keyboards import reply
from app.constants import EMERGENCY_KEYWORDS, EMERGENCY_MESSAGE, MEDICAL_DISCLAIMER
from app.database.repositories import ai_repo, user_repo
from app.services.ai_service import AIMessage, AIService
from app.utils.text import answer_long

router = Router(name="ai")


def _is_emergency(text: str) -> bool:
    low = (text or "").lower()
    return any(kw in low for kw in EMERGENCY_KEYWORDS)


AI_INTRO = (
    "🤖 <b>AI Murabbiy</b>\n\n"
    "Menga fitnes va sog'lom turmush haqida savol bering. Masalan:\n"
    "• Bugun qanday mashq qilay?\n"
    "• Uyda qanday shug'ullansam bo'ladi?\n"
    "• Qanday ovqatlansam bo'ladi?\n"
    "• Mashqni qanday to'g'ri bajaraman?\n\n"
    "Savolingizni shu yerga yozing 👇"
)


@router.message(F.text == reply.BTN_AI)
async def ai_intro(message: Message) -> None:
    await message.answer(AI_INTRO, reply_markup=reply.main_menu())


# Boshqa hech qanday holatda bo'lmagan va menyu tugmasi bo'lmagan matn — AI ga
@router.message(StateFilter(None), F.text & ~F.text.startswith("/"))
async def ai_question(message: Message, session, db_user, ai_service: AIService) -> None:
    text = message.text or ""

    # 1) Shoshilinch holat tekshiruvi — AI ga bormaydi
    if _is_emergency(text):
        await message.answer(EMERGENCY_MESSAGE, reply_markup=reply.main_menu())
        return

    # 2) Profil va tarix
    profile = await get_completed_profile(session, db_user)
    history_rows = await ai_repo.get_recent_messages(session, db_user.id, limit=6)
    history = [AIMessage(role=r.role, content=r.content) for r in history_rows]

    # 3) "yozayapti..." indikatori
    try:
        await message.bot.send_chat_action(message.chat.id, ChatAction.TYPING)
    except Exception:
        pass

    # 4) AI javobi (xato bo'lsa ham tushunarli matn qaytadi)
    answer = await ai_service.ask(text, profile=profile, history=history)

    # 5) Tarixni saqlaymiz (faqat AI yoqilgan bo'lsa mazmunli)
    if ai_service.enabled:
        await ai_repo.add_message(session, db_user.id, "user", text[:1500])
        await ai_repo.add_message(session, db_user.id, "assistant", answer[:2000])

    # 6) Ogohlantirish bilan javob
    footer = f"\n\n{MEDICAL_DISCLAIMER}" if ai_service.enabled else ""
    await answer_long(message, answer + footer, reply_markup=reply.main_menu())
