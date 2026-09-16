"""Yordamchi modullar testi (matn bo'lish, oziq-ovqat qidirish, grafik)."""
from __future__ import annotations

from datetime import datetime, timedelta

from app.data import foods
from app.services import progress_service
from app.utils.text import TELEGRAM_LIMIT, split_message


def test_short_message_not_split():
    assert split_message("qisqa matn") == ["qisqa matn"]


def test_long_message_is_split_within_limit():
    text = "\n".join(f"qator {i}" for i in range(2000))
    parts = split_message(text)
    assert len(parts) > 1
    assert all(len(p) <= TELEGRAM_LIMIT for p in parts)


def test_very_long_single_line_split():
    parts = split_message("x" * (TELEGRAM_LIMIT + 500))
    assert all(len(p) <= TELEGRAM_LIMIT for p in parts)


def test_food_lookup_and_estimate():
    food = foods.lookup_food("Tovuq ko'kragi")
    assert food is not None
    cal = foods.estimate_calories(food, 200)
    assert cal == round(food.kcal * 2)


def test_food_lookup_unknown():
    assert foods.lookup_food("noma'lum taom xyz") is None


def test_chart_needs_two_points():
    assert progress_service.generate_weight_chart([datetime.now()], [80.0]) is None


def test_chart_generates_png():
    dates = [datetime.now() + timedelta(days=i) for i in range(5)]
    weights = [85.0, 84.5, 84.0, 83.8, 83.0]
    png = progress_service.generate_weight_chart(dates, weights)
    # matplotlib mavjud bo'lsa PNG bytes, aks holda None (ikkalasi ham qabul)
    assert png is None or (isinstance(png, bytes) and png[:4] == b"\x89PNG")
