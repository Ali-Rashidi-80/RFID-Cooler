# نقشهٔ محصول تاب‌آور — کولر RFID چندمشتری (ایران)

**زبان‌ها:** [English](PRODUCT_ROADMAP_RESILIENCE.md) · **فارسی**

سند نیازسنجی و فیچرهای الزامی / رقابتی / اختیاری بر اساس تحقیق ThingsBoard، ESPHome/local-first، الگوی کنترل صنعتی ایران (SMS/BLE)، و محدودیت‌های شبکهٔ ملی.

## اصل معماری محصول پخته

```
لایه ۰ — همیشه: RFID + رله خشک + Learn (+ اختیاری کلید دیواری dry-contact)
لایه ۱ — LAN: SoftAP/Captive + HTTP محلی روی AP و روی IP استیشن
لایه ۱b — RF433 learn: ریموت فیزیکی بازار ایران (بدون اینترنت)
لایه ۲ — BLE: کنترل نزدیک با اپ/فلاتر بدون اینترنت
لایه ۳ — SMS/GSM: فرمان از راه دور وقتی دیتا قطع است
لایه ۴ — Cloud WSS: داشبورد چندمشتری (MQTT فقط R3 اختیاری)
همراه اختیاری — پریز/کنتاکتور بازار فقط ON/OFF تغذیهٔ کل (نه ۳سرعت)
```

**قانون طلایی:** قطع هر لایهٔ بالاتر هرگز لایهٔ پایین‌تر را از کار نیندازد.

---

## شکاف نسبت به ThingsBoard (و هدف «کامل‌تر برای این دامنه»)

| قابلیت ThingsBoard | وضعیت فعلی ما | اولویت محصول کولر |
|--------------------|---------------|-------------------|
| Device registry + credentials | هست (per-device token) | نگه‌داشت |
| Telemetry + dashboards | جزئی (status WS + Next.js) | P1 گسترش |
| RPC دوطرفه | SET_MODE/CYCLE | P0 نگه + ACK |
| Rule engine / alarms | ندارد | P1 (دما، قطع دستگاه، مصرف) |
| Local buffer هنگام قطع نت | **هست** (`outbox.py` / `outbox.jsonl`) | نگه‌داشت |
| Gateway + MQTT | اختیاری R3 (`mqtt_client.py`) | اختیاری |
| Multi-tenant | هست | نگه‌داشت + سخت‌گیری بیشتر |
| OTA | stub/مستند (`ota_stub.py` + `docs/OTA.md`) | P2 پس از پایداری |
| Offline edge UX | SoftAP/HTTP/wall/RF/BLE/SMS (کد)؛ Flutter field BLE+LAN | نگه‌داشت + bench سخت‌افزار |
| SMS در ایران | Melipayamak هشدار ابری + SIM800 فرمان (SKU) | نگه‌داشت |
| بومی‌سازی شبکه (میرور) | cooler-web + Vite `.npmrc` + pip/docker | نگه‌داشت |

ما نباید کل ThingsBoard را کپی کنیم؛ باید در **کنترل کولر آبی + چندمستأجر + تاب‌آوری ایران** جلوتر باشیم: local-first واقعی، SMS/BLE، و UX فارسی/Flutter.

---

## کانال‌های کنترل — گلچین بازار ایران (Must / Should / Optional / Reject)

تحقیق: دیجی‌کالا مگ کلید هوشمند کولر؛ Tuya/Sonoff/آسانه/جابان/لکسیت (WiFi+RF)؛ پریز ریموتی ۴۳۳؛ محدودیت Nest/پریز تک‌رله برای موتور القایی.

### Must
1. **RFID محلی** (موجود)
2. **Cloud WSS چندمشتری** (موجود) + **ACK/outbox** (پیاده‌شده)
3. **SoftAP + Captive + وب محلی (PIN)** (پیاده‌شده)
4. **HTTP روی IP استیشن (LAN)** وقتی WiFi خانه وصل است (پیاده‌شده)
5. **RF433 learn** — لرن از HTTP محلی `/api/rf433/learn` + نگاشت دکمه (پیاده‌شده؛ بهترین‌تلاش)
6. **هشدار Melipayamak** قطع دستگاه (بک‌اند `cooler_alerts`)

### Should
7. **Dry-contact کلید دیواری** موازی Off/Slow/Fast (**فاز R1 اختیاری** با `wall_enabled`)
8. **BLE GATT + PIN** + اسکچ Flutter (**R2**)
9. **SIM800 SMS فرمان** (SKU جدا — **R2**)
10. **Audit با channel** کامل (**R1 شروع، تکمیل با هر کانال**)

### Optional
11. **پریز/رلهٔ بازار فقط ON/OFF تغذیهٔ کل** پشت کنتاکتور — نه ۳سرعت
12. زمان‌بندی ابری (API)، MQTT اختیاری، Flutter field BLE+LAN؛ **ترموستات دما و OTA واقعی هنوز deferred** (`temp_enabled` بدون سنسور؛ `ota_stub`)

### Reject
- پریز هوشمند خانگی به‌عنوان کنترل اصلی کند/تند (بار القایی + تک‌رله)
- Nest/ترموستات ۲۴V مستقیم روی موتور
- وابستگی اجباری به کلود Tuya/eWeLink
- Zigbee به‌عنوان کانال اصلی ایران (سهم بازار کلید کولر = WiFi+RF)

### موضع پریز کنترلی
پریز ریموتی بازار برای پمپ/روشنایی رایج است؛ برای کولر آبی ۳حالته **جایگزین هسته نیست**. UX سادهٔ همان بازار با **لرن ریموت ۴۳۳ روی کنترلر ما** + هستهٔ dry-switch پوشش داده می‌شود.

---

## فیچرهای محصول (ماتریس اولویت)

### P0 — ضدگلوله / تولید واقعی

| فیچر | چرا |
|------|-----|
| صف محلی فرمان و تله‌متری روی فلش | مثل event storage در TB Gateway |
| ACK برای SET_MODE (accepted/applied/rejected) | جلوگیری از UI دروغین |
| AP + وب محلی + HTTP روی LAN STA | قطع اینترنت؛ کنترل در خانه بدون کلود |
| میرور چابکان اول برای npm/pip/docker | شبکهٔ ملی |
| Watchdog سلامت کانال‌ها + reconnect + fanout offline | اعتماد کاربر (بدهی dual-mode) |
| هشدار Melipayamak قطع دستگاه | وقتی سرور اینترنت دارد |
| Audit لاگ فرمان (کی/از کجا/کدام کانال) | چندمشتری حقوقی |

### P1 — رقابتی / تکمیل پلتفرم (R2)

| فیچر | چرا |
|------|-----|
| RF433 learn ریموت بازار | الگوی Tuya/Sonoff WiFi+RF ایران |
| Dry-contact کلید دیواری | نگه داشتن UX سنتی |
| BLE کنترل نزدیک + PIN | کارگاه بدون WiFi |
| SMS GSM SIM800 فرمان | دیتا قطع؛ آنتن زنده |
| Flutter اسکچ BLE/LAN | موبایل فیلد |
| آلارم دما / زمان‌بندی | نیاز دیجی‌کالا/Tuya |
| Export گزارش مصرف/رویداد | B2B |

### P2 — اختیاری / فاز بعد

| فیچر | چرا |
|------|-----|
| MQTT + retain | استاندارد IoT / HA |
| OTA امن با rollback | عملیات ناوگان |
| Flutter کامل Cloud\|LAN\|BLE | مکمل Next.js |
| SKU Lite پریز/کنتاکتور ON/OFF | همراه تغذیه؛ نه ۳سرعت |
| انرژی‌سنج / CT clamp | تمایز رقابتی |
| Rule engine ساده (اگر دما>X → تند) | نزدیک TB بدون پیچیدگی کامل |

---

## نیازسنجی کاربر (جمع‌بندی تحقیق)

1. **قطع نت نباید کولر را بی‌کنترل کند** (local-first؛ مدل‌های فقط-WiFi بازار ضعیف‌اند).  
2. **ریموت فیزیکی ساده بدون گوشی** (RF433 بازار ایران — SKC / ریموت همراه Sonoff-Tuya).  
3. **کلید دیواری سنتی همچنان کار کند** (dry-contact موازی).  
4. **روشن قبل از رسیدن + تایمر/دما** (نیاز پرتکرار دیجی‌کالا/اپ‌ها).  
5. **چند مشتری / چند دستگاه** با ایزوله (SaaS B2B).  
6. **نصب آسان بدون لپ‌تاپ** → Captive Portal.  
7. **دانلود وابستگی از داخل کشور** → Chabokan اول.  
8. **شفافیت وضعیت** آنلاین/آفلاین و ACK اعمال فرمان.  
9. **ایمنی موتور** dry-switch؛ رد پریز تک‌رله به‌عنوان ۳سرعت.  

---

## پیشنهاد فازبندی پیاده‌سازی

### فاز R1 — Local Edge + بدهی dual-mode
1. Captive portal + وب AP + HTTP روی LAN STA  
2. Outbox + ACK؛ wall inputs اختیاری  
3. cooler-web reconnect + fanout offline  
4. هشدار Melipayamak؛ میرور چابکان  

### فاز R2 — RF433 + Near-field + SMS
1. RF433 learn ریموت بازار  
2. BLE + Flutter اسکچ BLE/LAN  
3. SIM800 فرمان (SKU جدا)  

### فاز R3 — Platform parity اختیاری
1. MQTT / schedules / thermostat  
2. OTA؛ Flutter کامل  
3. مستند SKU Lite پریز+کنتاکتور فقط ON/OFF  

---

## معیار موفقیت (per-phase)

- **پس از R1:** RFID + AP/LAN وب (+ wall)؛ ACK/outbox؛ offline فوری در UI؛ بیلد چابکان  
- **پس از R2:** + RF433 + BLE + SMS UART  
- **محصول نهایی:** گلچین Must+Should؛ dry-switch دست‌نخورده؛ پریز فقط تغذیهٔ اختیاری  

---

*ممیزی پاس ۳ نهایی ۲۰۲۶-۰۷-۲۰ — پلن sealed برای اجرا. منابع: ThingsBoard Gateway، MicroPython captive/aioble، ESPHome local-first، دیجی‌کالا مگ کلید کولر، Tuya/Sonoff WiFi+RF، iran.chabokan.net / mirror2.*
