# چک‌لیست bench سخت‌افزار و integration

**زبان‌ها:** [English](HARDWARE_BENCH.md) (پیش‌فرض) · **فارسی**

این چک‌لیست روی **ESP32 واقعی + RC522 + SSR + SPDT** و در صورت امکان بک‌اند `door_control` اجرا شود.  
CI روی host فقط قرارداد پروتکل را ثابت می‌کند — **این bench فیزیک و UX ناوگان را ثابت می‌کند**.

نتایج را در جدول پایین ثبت کنید. مراحل ایمنی را رد نکنید.

---

## ۰. پیش‌پرواز (الزامی)

| مرحله | کار | معیار قبولی |
|-------|-----|-------------|
| ۰.۱ | **قطع برق شهر** قبل از سیم‌کشی | کلید خاموش، مرده تأیید |
| ۰.۲ | **NC→کند**, **NO→تند**, SSR→فاز پمپ + COM مکانیکی | مطابق [README](../README.fa.md) |
| ۰.۳ | RC522 فقط **3.3V**؛ SPI پین‌های 5/18/23/19/4 | بوت بدون brownout |
| ۰.۴ | فلش MicroPython + همه `.py` | [`INSTALL.fa.md`](../INSTALL.fa.md) |
| ۰.۵ | `config.example.json` → `config.json` روی دستگاه | secret commit نشود |
| ۰.۶ | `MASTER_CARD_UID` (یک‌بار DEBUG_MODE) | UID روی سریال |
| ۰.۷ | لاگ سریال آماده | mpremote repl یا UART |

**توقف اگر:** رله مکانیکی با SSR روشن کلیک کند (سوئیچینگ تحت بار).

---

## ۱. لایه ۰ — هسته آفلاین (بدون WiFi)

`online_enabled: false` یا بدون WiFi.

| ID | تست | مراحل | انتظار |
|----|-----|-------|--------|
| L0-1 | بوت سرد | روشن بدون WiFi | RFID ≤۲ث؛ رله‌ها OFF امن |
| L0-2 | ضربه کوتاه مستر | <۴ث | چرخه Off→کند→تند→Off |
| L0-3 | Kick-start | ورود به کند | ۳ث تند سپس خشک به کند |
| L0-4 | لغو kick-start | ضربه در ۳ث | force_off؛ OFF امن |
| L0-5 | ورود Learn | نگه‌داشت ۴ث مستر | موتور OFF؛ Learn true |
| L0-6 | add/remove کارت | دو بار اسکن در Learn | cards.json؛ بازیابی از tmp |
| L0-7 | خروج Learn | ضربه کوتاه یا ۱۵ث | Learn false |
| L0-8 | کارت ناشناس | خارج Learn | بوق deny؛ بدون حرکت |
| L0-9 | ضربه سریع | ۳+ ضربه | بدون task گیرکرده |

---

## ۲. invariantهای dry-switch (ایمنی)

| ID | تست | مشاهده | انتظار |
|----|-----|--------|--------|
| DS-1 | SSR خاموش قبل از mech | LED/scope رله mech | mech فقط با SSR off |
| DS-2 | مسیر کند | حالت کند | SSR ON، mech OFF |
| DS-3 | مسیر تند | حالت تند | SSR ON، mech ON |
| DS-4 | خاموش | Off | هر دو OFF |
| DS-5 | قطع برق وسط توالی | kick-start | بوت امن؛ بدون هر دو مسیر ON |

---

## ۳. dual-mode آنلاین (نیاز به بک‌اند)

پیش‌نیاز: کولر در `cooler-web` + token؛ `online_enabled: true`؛ WiFi و server درست.

| ID | تست | انتظار |
|----|-----|--------|
| WSS-1 | اتصال | `[WS] Connected`؛ داشبورد online |
| WSS-2 | status uplink | state و learn_mode درست |
| WSS-3 | SET_MODE کند | ACK accepted→applied؛ kick-start |
| WSS-4 | SET_MODE تند | ACK؛ موتور تند |
| WSS-5 | SET_MODE Off | ACK؛ خاموش |
| WSS-6 | CYCLE | چرخه ۰→۱→۲→۰ |
| WSS-7 | Learn + remote | ACK rejected learn_mode |
| WSS-8 | OPEN درب | بدون حرکت موتور |
| WSS-9 | RFID با WiFi قطع | RFID کار می‌کند |
| WSS-10 | reconnect | drain outbox |
| WSS-11 | outbox | backlog بدون حرکت تکراری موتور |

مرجع پروتکل: [README](../README.fa.md)

---

## ۴. لبه محلی (اختیاری)

### SoftAP / LAN HTTP / دیواری / RF433 / BLE / SMS / MQTT

همان IDهای نسخهٔ انگلیسی — فقط کانال‌های سیم‌کشی‌شده را تیک بزنید.

| کانال | smoke |
|-------|-------|
| SoftAP | PSK از local_pin؛ captive HTML |
| LAN | `/api/status`؛ PIN اشتباه → 401 |
| Wall | Off/Slow/Fast dry-contact |
| RF433 | learn + trigger |
| BLE/SMS/MQTT | مطابق README |

---

## ۵. شکست و regression

| ID | سناریو | انتظار |
|----|--------|--------|
| F-1 | WiFi قطع وسط SET_MODE | توالی محلی تمام یا abort امن |
| F-2 | token بد | WS fail؛ RFID OK |
| F-3 | فقط cards.tmp بعد قطع برق | boot از tmp |
| F-4 | WDT | بدون hang دائمی |
| F-5 | OPEN | هرگز حرکت کولر ندهد |

---

## ۶. ثبت sign-off

| تاریخ | اپراتور | ref فریم‌ور | ref بک‌اند | L0 | DS | WSS | Edge | یادداشت |
|-------|---------|-------------|------------|----|----|-----|------|---------|
| | | | | ☐ | ☐ | ☐ | ☐ | |

**تعریف done:** L0+DS سبز؛ WSS-1…11 اگر fleet آنلاین؛ edge برای کانال‌های فعال؛ F-1…5.

---

## دستورات سریع

```bash
python scripts/validate.py
python scripts/run_tests.py
mpremote connect COM3 fs cp main.py :main.py
mpremote connect COM3 reset
```

---

*host tests + این bench = منطق firmware + قرارداد بک‌اند؛ ایمنی برق شهر مسئولیت اپراتور است.*
