# راهنمای گام‌به‌گام bench سخت‌افزار

**زبان‌ها:** [English](BENCH_WALKTHROUGH.md) (پیش‌فرض) · **فارسی**

راهنمای عملی **A** — هر مرحله را تیک بزنید؛ [HARDWARE_BENCH.fa.md](HARDWARE_BENCH.fa.md) ماتریس pass/fail است.

---

## قبل از شروع

```powershell
cd D:\0\RFID-Cooler
python scripts/validate.py
python scripts/run_tests.py
pip install mpremote
pip install -r requirements-dev.txt
```

ایمنی برق شهر — قفل breaker / برقکار.

---

## فاز ۱ — فلش و سریال (~۱۵ دقیقه)

```powershell
cd D:\0\RFID-Cooler
.\scripts\bench_live.ps1                    # تشخیص COM
.\scripts\flash_device.ps1 -Port COM3     # فلش همه firmware
.\scripts\flash_device.ps1 -Port COM3 -IncludeConfig   # + config bench
.\scripts\bench_live.ps1 -Port COM3 -Snapshot          # لاگ ۱۰ث
```

**انتظار:** `[HW] RFID Initialized` و `[SYS] Cloud WSS disabled`

---

## فاز ۲ — UID مستر و L0 آفلاین (~۲۰ دقیقه)

1. یک‌بار `DEBUG_MODE = True` → UID کارت‌ها → `MASTER_CARD_UID` → `False`
2. بدون WiFi / `online_enabled: false`
3. L0-1 … L0-8 طبق [HARDWARE_BENCH.fa.md §1](HARDWARE_BENCH.fa.md)

---

## فاز ۳ — dry-switch (~۱۰ دقیقه)

DS-1 … DS-4 — اگر mech تحت بار کلیک کرد **توقف**.

---

## فاز ۴ — آنلاین با mock backend (~۲۵ دقیقه)

**ترمینال A:**

```powershell
python scripts/integration/mock_ws_backend.py --interactive --port 8765
```

**config bench:** [`config.bench.example.json`](../config.bench.example.json) — `server_host` = IP LAN کامپیوتر

```json
"server_host": "192.168.1.50",
"server_port": 8765,
"use_ssl": false,
"hardware_token": "bench-token",
"device_id": "bench-001",
"online_enabled": true
```

**دستورات mock:** `status` | `set 0|1|2` | `cycle` | `open`

| ID | mock | سریال دستگاه |
|----|------|--------------|
| WSS-1 | connect | `[WS] Connected` |
| WSS-3 | `set 1` | ACK accepted → applied |
| WSS-7 | Learn روی دستگاه + `set 1` | rejected learn_mode |
| WSS-8 | `open` | rejected |

---

## فاز ۵ — بک‌اند واقعی door_control

1. کولر در cooler-web → token + device_id  
2. `use_ssl: true`, پورت 443  
3. تست WSS-1…11 از داشبورد  

```powershell
python scripts/integration/probe_device_session.py `
  --host SERVER --port 443 --use-ssl true `
  --token TOKEN --device-id cooler-001 --send-get-status
```

---

## فاز ۶ — کانال‌های اختیاری

SoftAP / LAN HTTP / دیواری / RF433 — فقط اگر سیم‌کشی و flag فعال است.

---

## فاز ۷ — sign-off

جدول [HARDWARE_BENCH.fa.md §6](HARDWARE_BENCH.fa.md) +:

```powershell
git rev-parse --short HEAD
python scripts/integration/run_integration.py
```

---

## عیب‌یابی

| علامت | علت | رفع |
|-------|-----|-----|
| بدون `[WS] Connected` | IP/SSL | mock: `use_ssl false` |
| RFID خاموش | 3.3V/SPI | سیم RC522 |
| ACK بدون applied | Learn | خروج از Learn |

**بعدی:** [INTEGRATION.fa.md](INTEGRATION.fa.md)
