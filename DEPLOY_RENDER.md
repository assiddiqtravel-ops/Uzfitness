# 🚀 Render'ga deploy qilish — UzFit AI

Render — Telegram bot uchun **juda mos** platforma (Vercel'dan yaxshi):
doimiy ishlaydi, SQLite/persistent disk, reminderlar va polling to'liq ishlaydi.

Ikki variant bor:

- **A) Background Worker (tavsiya)** — polling, hammasi ishlaydi. Pullik (~$7/oy).
- **B) Web Service + Webhook (bepul mumkin)** — cheklovlar bilan.

---

## A) Background Worker (tavsiya) — polling

Bu eng oddiy va to'liq ishlaydigan usul. `render.yaml` (Blueprint) tayyor.

### Qadamlar
1. Kodni GitHub'ga push qiling (allaqachon qilingan).
2. [render.com](https://render.com) → **New +** → **Blueprint**.
3. Ushbu repozitoriyni tanlang. Render `render.yaml` ni o'qiydi va
   `uzfit-ai` nomli **Worker** yaratadi.
4. **Environment** bo'limida maxfiy qiymatlarni kiriting:
   - `BOT_TOKEN` = BotFather bergan token (**avval `/revoke` qilib yangilang!**)
   - (ixtiyoriy) `AI_PROVIDER=openai` va `OPENAI_API_KEY` (yoki anthropic)
   - (ixtiyoriy) `ADMIN_IDS=` sizning Telegram ID ingiz
5. **Create** bosing. Render `pip install` qilib, `python -m app.main` ni
   ishga tushiradi.
6. Loglar (Dashboard → Logs) da `Polling rejimida ishga tushdi` chiqsa —
   bot tayyor. Telegram'da `/start` yuboring.

> **Disk:** `render.yaml` da 1GB disk `data/` ga ulanadi — SQLite bazasi
> qayta deploy va restartlarda saqlanadi. Reminderlar ham ishlaydi.

> **Muhim:** Worker va Disk — Render'ning pullik rejalarida. Bepul variant
> uchun B bo'limiga qarang.

---

## B) Web Service + Webhook (bepul rejada mumkin)

Bepul **Web Service** ishlatiladi. Bepul rejada:
- Xizmat 15 daqiqa harakatsizlikdan keyin "uxlaydi"; yangi xabar (webhook POST)
  uni uyg'otadi, lekin birinchi javob sekin bo'lishi mumkin.
- **Reminderlar bepul rejada ishonchli emas** (xizmat uxlab qolsa scheduler
  to'xtaydi).
- Bepul rejada disk yo'q → **Render bepul Postgres** ishlating.

### Qadamlar
1. Render → **New +** → **PostgreSQL** (Free) yarating. `Internal Database URL`
   ni nusxalang (masalan `postgres://user:pass@host/db`).
   URL ni async formatga o'tkazing:
   `postgresql+asyncpg://user:pass@host/db`
2. Render → **New +** → **Web Service** → repozitoriyni tanlang. Sozlamalar:
   - **Root Directory:** bo'sh qoldiring
   - **Runtime / Language:** Python 3
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `python -m app.main`
   - **Instance Type:** **Free**
3. **Environment** ga quyidagilarni qo'shing:
   ```
   BOT_TOKEN=<token>
   RUN_MODE=webhook
   WEBHOOK_SECRET=<uzun-tasodifiy-satr>
   DATABASE_URL=postgresql+asyncpg://user:pass@host/db
   TIMEZONE=Asia/Tashkent
   ```
   > `WEBHOOK_URL` ni kiritish **shart emas** — kod Render bergan
   > `RENDER_EXTERNAL_URL` ni avtomatik oladi. `PORT` ham avtomatik.
   > (Xohlasangiz `WEBHOOK_URL=https://<service>.onrender.com` ni qo'lda
   > qo'shsangiz ham bo'ladi.)
4. Deploy tugagach, bot avtomatik `setWebhook` chaqiradi. Loglarda
   `Webhook o'rnatildi: https://...onrender.com/webhook` chiqadi.
5. Telegram'da `/start` yuboring. (Birinchi javob "uyqudan" uyg'onish uchun
   ~30–60 soniya kechikishi mumkin.)

> **Health-check:** xizmat `/` va `/healthz` da 200 qaytaradi, shuning uchun
> Render uni "live" deb ko'radi.

> **Postgres uchun** `asyncpg` allaqachon `requirements.txt` da bor.

---

## Tekshirish

- Render → Logs: xato bormi ko'ring.
- `Unauthorized` xatosi → `BOT_TOKEN` noto'g'ri yoki eskirgan (BotFather'da
  `/revoke` qilib yangilang).
- Bot javob bermasa → Worker/Service `Running` holatida ekanini va loglarda
  xato yo'qligini tekshiring.

## Reminderlar haqida
- **Worker (A)** da reminderlar to'liq ishlaydi.
- **Bepul Web Service (B)** da xizmat uxlab qolishi mumkin, shuning uchun
  reminderlar ishonchli emas. Ishonchli reminder kerak bo'lsa — Worker (A)
  yoki VPS ishlating.
