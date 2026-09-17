"""Ilova konfiguratsiyasi — environment variables orqali (pydantic-settings)."""
from __future__ import annotations

from functools import lru_cache
from typing import List

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Barcha sozlamalar .env yoki environment variables dan o'qiladi."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # Telegram
    bot_token: str = Field(default="", alias="BOT_TOKEN")

    # AI
    ai_provider: str = Field(default="none", alias="AI_PROVIDER")
    openai_api_key: str = Field(default="", alias="OPENAI_API_KEY")
    anthropic_api_key: str = Field(default="", alias="ANTHROPIC_API_KEY")
    ai_model: str = Field(default="gpt-4o-mini", alias="AI_MODEL")
    ai_timeout: int = Field(default=30, alias="AI_TIMEOUT")
    ai_max_tokens: int = Field(default=800, alias="AI_MAX_TOKENS")

    # Admin
    admin_ids_raw: str = Field(default="", alias="ADMIN_IDS")

    # Database
    database_url: str = Field(
        default="sqlite+aiosqlite:///data/uzfit.db", alias="DATABASE_URL"
    )

    # Vaqt zonasi
    timezone: str = Field(default="Asia/Tashkent", alias="TIMEZONE")

    # Ishga tushirish rejimi
    run_mode: str = Field(default="polling", alias="RUN_MODE")
    webhook_url: str = Field(default="", alias="WEBHOOK_URL")
    webhook_path: str = Field(default="/webhook", alias="WEBHOOK_PATH")
    webhook_host: str = Field(default="0.0.0.0", alias="WEBHOOK_HOST")
    webhook_port: int = Field(default=8080, alias="WEBHOOK_PORT")
    webhook_secret: str = Field(default="", alias="WEBHOOK_SECRET")

    # Log
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    @field_validator("ai_provider")
    @classmethod
    def _normalize_provider(cls, v: str) -> str:
        v = (v or "none").strip().lower()
        if v not in {"none", "openai", "anthropic"}:
            return "none"
        return v

    @field_validator("database_url")
    @classmethod
    def _normalize_database_url(cls, v: str) -> str:
        """DATABASE_URL ni tozalaydi va Postgres uchun async driverga keltiradi.

        Render/Heroku va boshqalar `postgres://` yoki `postgresql://` ko'rinishida
        beradi; bizga async `postgresql+asyncpg://` kerak. Shuningdek atrofdagi
        bo'shliqlar/yangi qatorni olib tashlaymiz (nusxa-joylashda bexosdan
        qo'shilib, autentifikatsiyani buzishi mumkin). Bu tufayli Render bergan
        URL ni o'zgartirmasdan yopishtirsa ham bo'ladi.
        """
        v = (v or "").strip()
        if v.startswith("postgres://"):
            v = "postgresql+asyncpg://" + v[len("postgres://"):]
        elif v.startswith("postgresql://"):
            v = "postgresql+asyncpg://" + v[len("postgresql://"):]
        return v

    @property
    def admin_ids(self) -> List[int]:
        """ADMIN_IDS ni intlar ro'yxatiga aylantiradi."""
        ids: List[int] = []
        for part in self.admin_ids_raw.split(","):
            part = part.strip()
            if part.isdigit():
                ids.append(int(part))
        return ids

    @property
    def ai_enabled(self) -> bool:
        """AI provayder yoqilgan va kalit mavjudligini tekshiradi."""
        if self.ai_provider == "openai":
            return bool(self.openai_api_key)
        if self.ai_provider == "anthropic":
            return bool(self.anthropic_api_key)
        return False

    def is_admin(self, user_id: int) -> bool:
        return user_id in self.admin_ids


@lru_cache
def get_settings() -> Settings:
    """Sozlamalarni bir marta yuklab, keshlangan holda qaytaradi."""
    return Settings()
