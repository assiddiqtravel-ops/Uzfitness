# ▲ Vercel'ga deploy qilish — UzFit AI (webhook, serverless)

> ⚠️ **Diqqat:** Vercel serverless bo'lgani uchun bot uchun **ideal emas**.
> Quyidagi cheklovlarni tushunib ish tuting. Ishonchliroq variant — **Render**
> (DEPLOY_RENDER.md) yoki **VPS**.

## Cheklovlar
1. **SQLite saqlanmaydi** → tashqi **Postgres** shart (Neon/Supabase — bepul).
2. **FSM (ro'yxatdan o'tish, suv/vazn kiritish)** uchun **Redis** shart
   (Upstash — bepul). Redis bo'lmasa ko'p bosqichli oqimlar ishlamaydi.
3. **Reminderlar ISHLAMAYDI** (doimiy jarayon/scheduler yo'q). Kerak bo'lsa
   tashqi cron ishlating yoki Render/VPS ga o'ting.
4. Faqat **webhook** rejimi.

## Kerakli servislar (bepul)
- **Postgres:** [neon.tech](https://neon.tech) yoki [supabase.com](https://supabase.com)
  → connection string oling.
- **Redis:** [upstash.com](https://upstash.com) → Redis DB yarating → `redis://...` URL oling.

## Qadamlar
1. Kodni GitHub'ga push qiling (qilingan).
2. [vercel.com](https://vercel.com) → **Add New** → **Project** → repozitoriyni import qiling.
3. **Environment Variables** ga qo'shing:
   ```
   BOT_TOKEN=<token>                       # BotFather (avval /revoke qiling!)
   DATABASE_URL=postgresql+asyncpg://user:pass@host/dbname
   REDIS_URL=redis://default:pass@host:port
   WEBHOOK_SECRET=<uzun-tasodifiy-satr>
   AI_PROVIDER=none                        # yoki openai/anthropic + kalit
   TIMEZONE=Asia/Tashkent
   ```
   > **Postgres URL** albatta `postgresql+asyncpg://` bilan boshlansin
   > (oddiy `postgres://` emas).
4. **Deploy** bosing.
5. Deploy tugagach, webhookni o'rnating — brauzerda oching:
   ```
   https://<sizning-loyiha>.vercel.app/api/set_webhook
   ```
   `{"ok": true, ...}` chiqsa — webhook o'rnatildi.
   (Yoki qo'lda: `https://api.telegram.org/bot<TOKEN>/setWebhook?url=https://<loyiha>.vercel.app/api/webhook&secret_token=<SECRET>`)
6. Telegram'da `/start` yuboring.

## Fayllar (Vercel uchun)
- `api/webhook.py` — Telegram update'larni qabul qiluvchi serverless funksiya.
- `api/set_webhook.py` — webhookni o'rnatuvchi yordamchi endpoint.
- `vercel.json` — funksiya sozlamalari.

## Muammolarni bartaraf etish
- **Bot javob bermayapti:** Vercel → Deployments → Functions → Logs ni ko'ring.
- **Ro'yxatdan o'tish o'rtada uzilyapti:** `REDIS_URL` o'rnatilmagan. Upstash
  Redis qo'shing.
- **DB xatosi:** `DATABASE_URL` `postgresql+asyncpg://` formatida ekanini
  tekshiring va `asyncpg` o'rnatilganini (`requirements.txt` da bor).
- **Bundle juda katta (build xatosi):** `requirements.txt` dan `matplotlib`
  qatorini olib tashlang — grafik o'rniga matnli hisobot ishlaydi.
