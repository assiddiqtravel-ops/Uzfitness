#!/usr/bin/env bash
# UzFit AI — SessionStart hook.
# Web sessiyalarida testlar va linterlar ishlashi uchun muhitni tayyorlaydi:
# virtual muhit yaratadi va kutubxonalarni o'rnatadi (idempotent).
set -euo pipefail

cd "$(dirname "$0")/../.." || exit 0

# Virtual muhit
if [ ! -d ".venv" ]; then
  python3 -m venv .venv >/dev/null 2>&1 || python -m venv .venv >/dev/null 2>&1 || true
fi

if [ -f ".venv/bin/pip" ]; then
  ./.venv/bin/pip install --quiet --upgrade pip >/dev/null 2>&1 || true
  ./.venv/bin/pip install --quiet -r requirements.txt >/dev/null 2>&1 || true
fi

# Test uchun minimal env (haqiqiy token shart emas)
if [ ! -f ".env" ]; then
  cp .env.example .env 2>/dev/null || true
fi

echo "UzFit AI muhiti tayyor. Testlar: ./.venv/bin/python -m pytest -q"
