# OTA (R3 — معوق؛ فقط stub)

**وضعیت صادقانه:** OTA امضاشده/خودکار در فریم‌ور **نیست**. `ota_stub.py` در صورت فراخوانی `ota_not_implemented` برمی‌گرداند. تا انتشار R3 اختصاصی OTA ناوگان انتظار نداشته باشید.

## گردش کار به‌روزرسانی امن (امروز)

1. outbox را خالی کنید / دستگاه آنلاین و ACK سالم باشد.
2. روی PC با ابزار چابکان-اول، فایل‌های `.py` تأییدشده آماده کنید.
3. کپی آفلاین:

```bash
mpremote connect COM3 fs cp main.py :main.py
mpremote connect COM3 reset
```

4. کپی known-good قبلی را برای rollback نگه دارید.

## آینده (ارسال نشده)

- pull HTTPS باندل امضاشده + پارتیشن rollback
- block OTA در Learn Mode یا dry-switch فعال

**زبان‌ها:** [English](OTA.md) · [Persian](OTA.fa.md)
