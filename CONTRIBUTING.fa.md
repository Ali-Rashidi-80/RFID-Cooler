# راهنمای مشارکت

**زبان‌ها:** [English](CONTRIBUTING.md) (پیش‌فرض) · **فارسی**

1. تغییرات **اتمیک** باشند؛ قبل از PR: `python scripts/validate.py`.
2. **انگلیسی منبع حقیقت مستندات است.** فایل‌های `.fa.md` باید با واقعیت هم‌راستا بمانند.
3. هرگز secret commit نکنید: `config.json`، توکن، کارت‌ها، رمز WiFi.
4. ادعاهای GPIO/سیم‌کشی باید با `main.py` یکی باشند.
5. ایمنی dry-switch را برای راحتی ضعیف نکنید.
6. `test/test_ssrRelay.py` اسکریپت آزمایشگاه قدیمی است، نه gate محصول.

## چک‌لیست PR

- [ ] `python scripts/validate.py` سبز
- [ ] بدون secret در diff
- [ ] README / INSTALL به‌روز اگر رفتار کاربر تغییر کرده
- [ ] `.fa.md` فارسی به‌روز

## سبک commit

- فعل امری (~۷۲ کاراکتر): `Add LAN HTTP status endpoint docs`
- بدنه: **چرا**، نه فقط چه چیزی عوض شد.

## دستورات

```bash
python scripts/validate.py
mpremote connect COM3 fs cp main.py :main.py
mpremote connect COM3 reset
```

## تغییر سخت‌افزار

اگر timing رله یا pinout عوض شد:

1. ثابت‌های `main.py`
2. جداول README (EN + FA)
3. در صورت نیاز، چک‌لیست سخت‌افزار
