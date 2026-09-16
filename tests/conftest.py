"""Pytest fixtures — test uchun in-memory DB va yordamchi obyektlar."""
from __future__ import annotations

import os
from types import SimpleNamespace

import pytest
import pytest_asyncio

# Test uchun minimal env (config yuklanishi uchun)
os.environ.setdefault("BOT_TOKEN", "test-token")
os.environ.setdefault("AI_PROVIDER", "none")
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.database.models import Base


@pytest_asyncio.fixture
async def engine():
    """Har bir test uchun alohida in-memory SQLite engine."""
    eng = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield eng
    await eng.dispose()


@pytest_asyncio.fixture
async def sessionmaker(engine):
    return async_sessionmaker(engine, expire_on_commit=False)


@pytest_asyncio.fixture
async def session(sessionmaker):
    async with sessionmaker() as s:
        yield s
        await s.commit()


@pytest.fixture
def sample_profile():
    """Testlar uchun namunaviy profil obyekti."""
    return SimpleNamespace(
        name="Ali",
        age=30,
        gender="male",
        height_cm=178.0,
        weight_kg=85.0,
        start_weight_kg=85.0,
        goal="weight_loss",
        location="home",
        days_per_week=3,
        experience="beginner",
        activity_level="medium",
        diet_type="no_restrictions",
        allergies=None,
        equipment="gantel",
        health_notes=None,
    )
