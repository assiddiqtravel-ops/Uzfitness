"""Loglash sozlamalari — maxfiy ma'lumotlarni yashiradi."""
from __future__ import annotations

import logging
import re
import sys

# Loglarda tasodifan chiqib qolishi mumkin bo'lgan maxfiy naqshlar
_SECRET_PATTERNS = [
    re.compile(r"(bot)?\d{6,}:[A-Za-z0-9_-]{30,}"),  # Telegram bot token
    re.compile(r"sk-[A-Za-z0-9_-]{20,}"),            # OpenAI kalitlari
    re.compile(r"sk-ant-[A-Za-z0-9_-]{20,}"),        # Anthropic kalitlari
]


class SecretRedactingFilter(logging.Filter):
    """Log yozuvlaridagi tokenlar/kalitlarni maskalaydi."""

    def filter(self, record: logging.LogRecord) -> bool:
        try:
            msg = record.getMessage()
        except Exception:
            return True
        redacted = msg
        for pattern in _SECRET_PATTERNS:
            redacted = pattern.sub("***REDACTED***", redacted)
        if redacted != msg:
            record.msg = redacted
            record.args = ()
        return True


def setup_logging(level: str = "INFO") -> None:
    """Ildiz loggerni sozlaydi."""
    log_level = getattr(logging, level.upper(), logging.INFO)

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(
        logging.Formatter(
            "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    )
    handler.addFilter(SecretRedactingFilter())

    root = logging.getLogger()
    root.handlers.clear()
    root.setLevel(log_level)
    root.addHandler(handler)

    # Juda shovqinli kutubxonalarni tinchlantirish
    logging.getLogger("aiogram.event").setLevel(logging.WARNING)
    logging.getLogger("aiosqlite").setLevel(logging.WARNING)
    logging.getLogger("apscheduler").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
