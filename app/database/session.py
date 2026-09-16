"""Async database engine va sessiya boshqaruvi."""
from __future__ import annotations

import os
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncIterator, Optional

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.database.models import Base

_engine: Optional[AsyncEngine] = None
_sessionmaker: Optional[async_sessionmaker[AsyncSession]] = None


def _ensure_sqlite_dir(database_url: str) -> None:
    """SQLite fayli uchun papka mavjudligini ta'minlaydi."""
    prefix = "sqlite+aiosqlite:///"
    if database_url.startswith(prefix):
        db_path = database_url[len(prefix):]
        if db_path and db_path != ":memory:":
            Path(db_path).parent.mkdir(parents=True, exist_ok=True)


def init_engine(database_url: str) -> AsyncEngine:
    """Global engine va sessionmaker ni yaratadi (idempotent)."""
    global _engine, _sessionmaker
    if _engine is None:
        _ensure_sqlite_dir(database_url)
        _engine = create_async_engine(
            database_url,
            echo=False,
            pool_pre_ping=True,
        )
        _sessionmaker = async_sessionmaker(
            _engine, expire_on_commit=False, class_=AsyncSession
        )
    return _engine


def get_sessionmaker() -> async_sessionmaker[AsyncSession]:
    if _sessionmaker is None:
        raise RuntimeError("Database hali ishga tushmagan. Avval init_engine() chaqiring.")
    return _sessionmaker


async def init_db(database_url: str) -> None:
    """Jadvallarni yaratadi (agar mavjud bo'lmasa). Alembic ishlatilmasa qulay."""
    engine = init_engine(database_url)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def dispose_engine() -> None:
    global _engine, _sessionmaker
    if _engine is not None:
        await _engine.dispose()
        _engine = None
        _sessionmaker = None


@asynccontextmanager
async def session_scope() -> AsyncIterator[AsyncSession]:
    """Tranzaksiyali sessiya konteksti. Xatoda rollback qiladi."""
    sm = get_sessionmaker()
    session = sm()
    try:
        yield session
        await session.commit()
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()
