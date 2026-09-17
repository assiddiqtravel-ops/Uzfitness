"""Vercel yordamchi endpoint: Telegram webhookni shu deploy URL ga o'rnatadi.

Brauzerda <domen>/api/set_webhook manzilini oching (bir marta). U
setWebhook chaqiruvini bajaradi va natijani qaytaradi.

URL manbasi: WEBHOOK_URL env, aks holda Vercel bergan VERCEL_URL.
"""
from __future__ import annotations

import json
import os
import urllib.parse
import urllib.request
from http.server import BaseHTTPRequestHandler

from app.config import get_settings


class handler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:  # noqa: N802
        settings = get_settings()

        base = settings.webhook_url.strip()
        if not base:
            vercel_url = os.environ.get("VERCEL_URL", "").strip()
            base = f"https://{vercel_url}" if vercel_url else ""

        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.end_headers()

        if not settings.bot_token:
            self.wfile.write(json.dumps({"ok": False, "error": "BOT_TOKEN yo'q"}).encode())
            return
        if not base:
            self.wfile.write(
                json.dumps({"ok": False, "error": "WEBHOOK_URL yoki VERCEL_URL topilmadi"}).encode()
            )
            return

        hook_url = base.rstrip("/") + "/api/webhook"
        params = {"url": hook_url, "drop_pending_updates": "true"}
        if settings.webhook_secret:
            params["secret_token"] = settings.webhook_secret

        api = (
            f"https://api.telegram.org/bot{settings.bot_token}/setWebhook?"
            + urllib.parse.urlencode(params)
        )
        try:
            with urllib.request.urlopen(api, timeout=10) as resp:
                data = json.loads(resp.read().decode())
            data["_configured_webhook"] = hook_url
            self.wfile.write(json.dumps(data, ensure_ascii=False).encode("utf-8"))
        except Exception as exc:
            self.wfile.write(
                json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False).encode("utf-8")
            )
