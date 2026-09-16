"""Admin panel — statistika, foydalanuvchi qidirish, ommaviy xabar."""
from __future__ import annotations

import asyncio

from aiogram import Bot, F, Router
from aiogram.filters import BaseFilter, Command, CommandObject
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.bot.keyboards import inline, reply
from app.bot.states.registration import AdminBroadcast
from app.config import Settings
from app.database.repositories import stats_repo, user_repo
from app.utils.logging_config import get_logger

logger = get_logger(__name__)
router = Router(name="admin")


class IsAdmin(BaseFilter):
    """Foydalanuvchi admin ekanligini tekshiradi (settings.admin_ids)."""

    async def __call__(self, event, settings: Settings = None) -> bool:  # type: ignore[override]
        if settings is None:
            return False
        user = getattr(event, "from_user", None)
        return user is not None and settings.is_admin(user.id)


admin_only = IsAdmin()


@router.message(Command("admin"), admin_only)
async def admin_panel(message: Message) -> None:
    await message.answer(
        "🛠 <b>Admin panel</b>\n\n"
        "/stats — statistika\n"
        "/finduser &lt;telegram_id&gt; — foydalanuvchini qidirish\n"
        "/broadcast — ommaviy xabar yuborish (tasdiqlash bilan)\n"
    )


@router.message(Command("admin"))
async def admin_denied(message: Message, settings: Settings) -> None:
    # admin bo'lmaganlar uchun (yuqoridagi filtr o'tmaganda)
    await message.answer("⛔ Bu buyruq faqat administratorlar uchun.")


@router.message(Command("stats"), admin_only)
async def admin_stats(message: Message, session) -> None:
    total = await stats_repo.count_users(session)
    profiles = await stats_repo.count_completed_profiles(session)
    active_day = await stats_repo.count_active_users(session, days=1)
    active_week = await stats_repo.count_active_users(session, days=7)
    await message.answer(
        "📊 <b>Statistika</b>\n\n"
        f"• Jami foydalanuvchilar: <b>{total}</b>\n"
        f"• To'ldirilgan profillar: <b>{profiles}</b>\n"
        f"• Kunlik faol (24 soat): <b>{active_day}</b>\n"
        f"• Haftalik faol (7 kun): <b>{active_week}</b>\n"
    )


@router.message(Command("finduser"), admin_only)
async def admin_find_user(message: Message, command: CommandObject, session) -> None:
    arg = (command.args or "").strip()
    if not arg.isdigit():
        await message.answer("Foydalanish: /finduser <telegram_id>")
        return
    user = await stats_repo.find_user_by_telegram_id(session, int(arg))
    if user is None:
        await message.answer("Foydalanuvchi topilmadi.")
        return
    profile = await user_repo.get_profile(session, user.id)
    # Faqat zarur minimal ma'lumot
    lines = [
        "👤 <b>Foydalanuvchi</b>",
        f"• Telegram ID: <code>{user.telegram_id}</code>",
        f"• Ro'yxatdan o'tgan: {user.created_at:%Y-%m-%d}",
        f"• Oxirgi faollik: {user.last_active_at:%Y-%m-%d %H:%M} UTC",
        f"• Profil to'ldirilgan: {'ha' if (profile and profile.completed) else 'yo‘q'}",
        f"• Bloklangan: {'ha' if user.is_blocked else 'yo‘q'}",
    ]
    await message.answer("\n".join(lines))


# ---------------- Broadcast ----------------
@router.message(Command("broadcast"), admin_only)
async def broadcast_start(message: Message, state: FSMContext) -> None:
    await state.set_state(AdminBroadcast.message)
    await message.answer(
        "✍️ Yubormoqchi bo'lgan xabaringizni yozing.\n"
        "Bekor qilish uchun /cancel.",
        reply_markup=reply.cancel_only(),
    )


@router.message(AdminBroadcast.message, admin_only, F.text)
async def broadcast_preview(message: Message, state: FSMContext) -> None:
    text = message.text or ""
    await state.update_data(broadcast_text=text)
    await state.set_state(AdminBroadcast.confirm)
    await message.answer(
        f"Quyidagi xabar barcha foydalanuvchilarga yuboriladi:\n\n———\n{text}\n———\n\n"
        "Tasdiqlaysizmi?",
        reply_markup=inline.broadcast_confirm_kb(),
    )


@router.callback_query(AdminBroadcast.confirm, F.data == "bc:no")
async def broadcast_cancel(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.message.answer("Bekor qilindi.", reply_markup=reply.main_menu())
    await callback.answer()


@router.callback_query(AdminBroadcast.confirm, F.data == "bc:yes")
async def broadcast_send(callback: CallbackQuery, state: FSMContext, session, bot: Bot) -> None:
    data = await state.get_data()
    text = data.get("broadcast_text", "")
    await state.clear()
    if not text:
        await callback.answer("Xabar bo'sh.", show_alert=True)
        return

    user_ids = await stats_repo.get_all_user_ids(session)
    await callback.message.answer(f"📤 Yuborilmoqda... ({len(user_ids)} foydalanuvchi)")
    await callback.answer()

    sent = 0
    failed = 0
    for uid in user_ids:
        try:
            await bot.send_message(uid, text)
            sent += 1
        except Exception as exc:
            failed += 1
            logger.warning("Broadcast xato (user=%s): %s", uid, exc.__class__.__name__)
            # bloklagan foydalanuvchilarni belgilaymiz
            try:
                await stats_repo.mark_user_blocked(session, uid, True)
                await session.commit()
            except Exception:
                pass
        # Telegram rate limit (~30 msg/s) — ehtiyot uchun sekinlashtiramiz
        await asyncio.sleep(0.05)

    await callback.message.answer(
        f"✅ Yakunlandi.\n• Yuborildi: <b>{sent}</b>\n• Xato: <b>{failed}</b>",
        reply_markup=reply.main_menu(),
    )
