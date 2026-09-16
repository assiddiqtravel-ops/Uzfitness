"""Matn bilan ishlash yordamchilari (Telegram limitlari)."""
from __future__ import annotations

from typing import List

TELEGRAM_LIMIT = 4096


def split_message(text: str, limit: int = TELEGRAM_LIMIT) -> List[str]:
    """Uzun matnni Telegram limitiga mos bo'laklarga bo'ladi (qatorlar bo'yicha)."""
    if len(text) <= limit:
        return [text]
    parts: List[str] = []
    current = ""
    for line in text.split("\n"):
        # bitta qator limitdan uzun bo'lsa, uni majburan bo'lamiz
        while len(line) > limit:
            parts.append(line[:limit])
            line = line[limit:]
        if len(current) + len(line) + 1 > limit:
            if current:
                parts.append(current)
            current = line
        else:
            current = f"{current}\n{line}" if current else line
    if current:
        parts.append(current)
    return parts


async def answer_long(message, text: str, **kwargs) -> None:
    """Uzun matnni bo'lib yuboradi. reply_markup faqat oxirgi bo'lakka qo'yiladi."""
    parts = split_message(text)
    reply_markup = kwargs.pop("reply_markup", None)
    for i, part in enumerate(parts):
        is_last = i == len(parts) - 1
        await message.answer(
            part,
            reply_markup=reply_markup if is_last else None,
            **kwargs,
        )
