"""Barcha routerlarni to'g'ri tartibda yig'ish.

Tartib muhim: maxsus (menyu tugmalari, FSM, admin) routerlar AI ning catch-all
handleridan OLDIN kelishi kerak.
"""
from __future__ import annotations

from aiogram import Router

from app.bot.handlers import (
    admin,
    ai,
    checkin,
    errors,
    plans,
    progress,
    registration,
    settings,
    start,
    workout,
)


def build_root_router() -> Router:
    root = Router(name="root")
    root.include_router(errors.router)      # xato handleri
    root.include_router(start.router)       # /start, /cancel, start menyu
    root.include_router(registration.router)  # ro'yxatdan o'tish FSM
    root.include_router(admin.router)       # admin buyruqlar
    root.include_router(settings.router)    # sozlamalar/reminderlar
    root.include_router(plans.router)       # reja/profil ko'rsatish
    root.include_router(workout.router)     # bugungi mashg'ulot
    root.include_router(checkin.router)     # suv/vazn/ovqat/faollik
    root.include_router(progress.router)    # natijalar/hisobot
    root.include_router(ai.router)          # AI (catch-all — oxirida)
    return root
