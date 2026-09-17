# UzFit AI — Frontend (lending sahifa)

Bu — UzFit AI botining **statik promo (lending) sahifasi**. U Vercel'da
joylanadi va foydalanuvchini Telegram botga yo'naltiradi. Backend (bot) bilan
to'g'ridan-to'g'ri bog'lanmaydi — faqat "Botni ochish" tugmasi orqali havola.

## Sozlash
`web/index.html` ichidagi `BOT_URL` ni o'zingizning bot @username ingizga
o'zgartiring:
```js
var BOT_URL = "https://t.me/Uzfitnesbot";
```

## Vercel'ga deploy
Bu statik sahifa — build kerak emas.

1. [vercel.com](https://vercel.com) → **Add New** → **Project** → repozitoriyni import qiling.
2. **Root Directory** ni `web` qilib belgilang (muhim! shunda Vercel faqat shu
   papkani deploy qiladi, ildizdagi Python `api/` ga tegmaydi).
3. **Framework Preset:** Other (yoki "No Framework"). Build/Output bo'sh.
4. **Deploy** bosing. Vercel `https://<loyiha>.vercel.app` beradi.

Tayyor — sahifa ochiladi va "Boshlash" tugmasi botga olib boradi.
