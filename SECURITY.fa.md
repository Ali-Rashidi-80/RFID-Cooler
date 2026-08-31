# سیاست امنیت

**زبان‌ها:** [English](SECURITY.md) (پیش‌فرض) · **فارسی**

## نسخه‌های پشتیبانی‌شده

| نسخه | پشتیبانی |
|------|----------|
| شاخه main | best effort |

## گزارش آسیب‌پذیری

مسائل امنیتی را **خصوصی** گزارش کنید — issue عمومی با جزئیات exploit یا توکن زنده نسازید.

شامل:

- component affected
- مراحل بازتولید (توکن redact)
- اثر (کنترل موتور، نشت credential، bypass LAN)

هدف: پاسخ تا ۷ روز.

## یادداشت‌های scope

- **سیم‌کشی برق شهر** خارج از scope نرم‌افزار اما حیاتی — برقکار مجاز.
- **`local_pin` / PIN BLE / SMS** کانال محلی را محافظت می‌کنند؛ در تولید پیش‌فرض نگذارید.
- **`hardware_token`** per-device — مثل رمز؛ در نشت rotate کنید.
- **TLS MicroPython** ممکن است محدود باشد — WSS + توکن قوی.
- **Learn Mode** عمداً فرمان موتور از راه دور را block می‌کند.
- **`OPEN` درب** عمداً نادیده — اگر regression حرکت داد گزارش دهید.

## توسعه امن

- CI: `python scripts/validate.py`
- secretها در gitignore
- config نمونه فقط placeholder
