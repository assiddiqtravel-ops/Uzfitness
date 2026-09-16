"""/start, bot haqida, xavfsizlik, /help va /cancel."""
from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import Command, CommandStart, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.bot.keyboards import inline, reply
from app.constants import MEDICAL_DISCLAIMER
from app.database.repositories import user_repo

router = Router(name="start")


WELCOME_TEXT = (
    "👋 Assalomu alaykum! Men — <b>UzFit AI</b>, sizning shaxsiy fitnes yordamchingizman.\n\n"
    "Men sizga:\n"
    "• Shaxsiy mashg'ulot rejasini tuzishda,\n"
    "• Sog'lom ovqatlanish tavsiyalarini olishda,\n"
    "• Kundalik holatni kuzatib borishda,\n"
    "• AI murabbiy bilan maslahatlashishda yordam beraman.\n\n"
    "Boshlash uchun quyidagi tugmani bosing 👇"
)

ABOUT_TEXT = (
    "ℹ️ <b>UzFit AI haqida</b>\n\n"
    "UzFit AI — fitnesni endi boshlayotganlar, ortiqcha vaznini kamaytirmoqchi "
    "bo'lganlar va sog'lom turmush tarziga o'tmoqchi bo'lganlar uchun yaratilgan bot.\n\n"
    "Bot sizning ma'lumotlaringizga mos ravishda mashg'ulot va ovqatlanish "
    "tavsiyalarini beradi, kundalik natijalarni kuzatib boradi.\n\n"
    f"{MEDICAL_DISCLAIMER}"
)

PRIVACY_TEXT = (
    "🛡 <b>Xavfsizlik va maxfiylik</b>\n\n"
    "• Ma'lumotlaringiz faqat sizga xizmat ko'rsatish uchun ishlatiladi.\n"
    "• Har bir foydalanuvchi ma'lumoti Telegram ID orqali ajratiladi va "
    "boshqa foydalanuvchilarga ko'rsatilmaydi.\n"
    "• Tokenlar va maxfiy kalitlar bot kodida saqlanmaydi.\n"
    "• Siz istagan vaqtda profilingizni yangilashingiz mumkin.\n\n"
    f"{MEDICAL_DISCLAIMER}"
)


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext, session, db_user) -> None:
    await state.clear()
    profile = await user_repo.get_profile(session, db_user.id)
    if profile is not None and profile.completed:
        await message.answer(
            f"Xush kelibsiz, <b>{profile.name}</b>! 🎉\n\n"
            "Asosiy menyudan foydalanishingiz mumkin.",
            reply_markup=reply.main_menu(),
        )
    else:
        await message.answer(WELCOME_TEXT, reply_markup=inline.start_menu())


@router.callback_query(F.data == "start:about")
async def cb_about(callback: CallbackQuery) -> None:
    await callback.message.answer(ABOUT_TEXT)
    await callback.answer()


@router.callback_query(F.data == "start:privacy")
async def cb_privacy(callback: CallbackQuery) -> None:
    await callback.message.answer(PRIVACY_TEXT)
    await callback.answer()


@router.message(Command("help"))
async def cmd_help(message: Message) -> None:
    await message.answer(
        "<b>Yordam</b>\n\n"
        "/start — boshlash / asosiy menyu\n"
        "/cancel — joriy jarayonni bekor qilish\n"
        "/menu — asosiy menyuni ko'rsatish\n\n"
        "Menyudagi tugmalar orqali mashg'ulot, ovqatlanish, suv, vazn va natijalarni "
        "boshqarishingiz mumkin. Savol berish uchun «🤖 AI Murabbiy» tugmasidan "
        "foydalaning.",
        reply_markup=reply.main_menu(),
    )


@router.message(Command("menu"))
async def cmd_menu(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer("Asosiy menyu 👇", reply_markup=reply.main_menu())


@router.message(Command("cancel"))
@router.message(F.text == reply.BTN_CANCEL)
async def cmd_cancel(message: Message, state: FSMContext) -> None:
    current = await state.get_state()
    await state.clear()
    if current is None:
        await message.answer("Bekor qiladigan jarayon yo'q.", reply_markup=reply.main_menu())
    else:
        await message.answer("✅ Bekor qilindi.", reply_markup=reply.main_menu())


@router.callback_query(F.data == "reg:cancel")
async def cb_cancel(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.message.answer("✅ Bekor qilindi.", reply_markup=reply.main_menu())
    await callback.answer()
