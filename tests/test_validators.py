"""Input validatsiya testlari (yosh, bo'y, vazn, suv, ism)."""
from __future__ import annotations

import pytest

from app.utils import validators


@pytest.mark.parametrize("raw,ok", [
    ("25", True), ("10", True), ("100", True),
    ("9", False), ("101", False), ("abc", False), ("25.5", False), ("-5", False), ("", False),
])
def test_validate_age(raw, ok):
    assert validators.validate_age(raw).ok is ok


@pytest.mark.parametrize("raw,ok", [
    ("175", True), ("120", True), ("230", True), ("175.5", True),
    ("119", False), ("231", False), ("xyz", False), ("", False),
])
def test_validate_height(raw, ok):
    assert validators.validate_height(raw).ok is ok


@pytest.mark.parametrize("raw,ok", [
    ("70", True), ("72.5", True), ("72,5", True), ("30", True), ("300", True),
    ("29", False), ("301", False), ("og'ir", False), ("", False),
])
def test_validate_weight(raw, ok):
    res = validators.validate_weight(raw)
    assert res.ok is ok


def test_validate_weight_comma_parsing():
    res = validators.validate_weight("72,5")
    assert res.ok and res.value == 72.5


@pytest.mark.parametrize("raw,expected_ml,ok", [
    ("500", 500, True),
    ("500 ml", 500, True),
    ("0.5 l", 500, True),
    ("2 l", 2000, True),
    ("40", None, False),      # juda kam
    ("6000", None, False),    # juda ko'p
    ("suv", None, False),
])
def test_validate_water(raw, expected_ml, ok):
    res = validators.validate_water_ml(raw)
    assert res.ok is ok
    if ok:
        assert res.value == expected_ml


def test_validate_name():
    assert validators.validate_name("Ali").ok is True
    assert validators.validate_name("A").ok is False
    assert validators.validate_name("x" * 50).ok is False


def test_clean_name_strips_newlines():
    assert validators.clean_name("Ali\nValiyev\t") == "Ali Valiyev"


def test_days_per_week():
    assert validators.validate_days_per_week(3) is True
    assert validators.validate_days_per_week(7) is False
    assert validators.validate_days_per_week(1) is False
