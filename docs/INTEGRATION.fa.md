# تست integration (بک‌اند و automation)

**زبان‌ها:** [English](INTEGRATION.md) (پیش‌فرض) · **فارسی**

اسکریپت‌ها در `scripts/integration/` — **فقط PC**، روی ESP32 فلش نمی‌شوند.

---

## نصب

```bash
pip install -r requirements-dev.txt
```

متغیرهای env: `WS_HOST`, `WS_PORT`, `WS_USE_SSL`, `WS_TOKEN`, `WS_DEVICE_ID`

---

## اسکریپت‌ها

| اسکریپت | کار |
|---------|-----|
| `run_integration.py` | E2E خودکار بدون ESP32 — ACK accepted→applied |
| `mock_ws_backend.py` | mock کلود + `--interactive` برای bench |
| `probe_device_session.py` | probe سرور live/mock |

---

## ۱. integration خودکار

```bash
python scripts/integration/run_integration.py
```

---

## ۲. mock + ESP32 واقعی

ترمینال A:

```bash
python scripts/integration/mock_ws_backend.py --interactive --port 8765
```

config دستگاه: IP LAN کامپیوتر، `use_ssl: false`، پورت 8765.

راهنمای کامل: [BENCH_WALKTHROUGH.fa.md](BENCH_WALKTHROUGH.fa.md)

---

## ۳. probe بک‌اند door_control

```bash
python scripts/integration/probe_device_session.py \
  --host SERVER --port 443 --use-ssl true \
  --token TOKEN --device-id cooler-001 --send-get-status
```

**محدودیت:** بعضی سرورها فقط یک WS سخت‌افزار — probe ممکن است با دستگاه متصل تداخل کند.

---

## قرارداد پروتکل

Downlink: `SET_MODE` + `command_id` · uplink: `ACK` با `accepted|applied|rejected`

[README.fa.md](../README.fa.md)
