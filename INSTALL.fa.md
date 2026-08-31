# نصب و استقرار

**زبان‌ها:** [English](INSTALL.md) (پیش‌فرض) · **فارسی**

## پیش‌نیاز

| ابزار | کاربرد |
|-------|--------|
| [فریم‌ور MicroPython ESP32](https://micropython.org/download/ESP32_GENERIC/) | رانتایم دستگاه |
| [`mpremote`](https://docs.micropython.org/en/latest/reference/mpremote.html) | کپی فایل + reset |
| درایور USB سریال | برد ESP32 |

در ایران برای npm/pip داشبورد از میرور چابکان استفاده کنید — [`docs/IRAN_MIRRORS.fa.md`](docs/IRAN_MIRRORS.fa.md).

## ۱. فلش MicroPython

1. در صورت نیاز BOOT را نگه دارید؛ برد جدید یک‌بار erase.
2. `.bin` پایدار ESP32 Generic را فلش کنید.
3. REPL: `mpremote connect COM3 repl`

## ۲. آپلود فایل‌های فریم‌ور

```powershell
$port = "COM3"
$files = @(
  "boot.py","main.py","mfrc522.py",
  "wifi_manager.py","ap_manager.py","local_http.py","dns_captive.py",
  "outbox.py","cloud.py","ws_client.py",
  "wall_inputs.py","rf433.py","ble_control.py","sms_modem.py",
  "mqtt_client.py","ota_stub.py"
)
foreach ($f in $files) {
  mpremote connect $port fs cp $f ":$f"
}
mpremote connect $port reset
```

## ۳. پیکربندی

```powershell
copy config.example.json config.json
mpremote connect COM3 fs cp config.json :config.json
```

**فقط آفلاین:** `config.json` نگذارید یا `"online_enabled": false`.

## ۴. UID کارت مستر

1. یک‌بار `DEBUG_MODE = True` در `main.py`.
2. فلش، کارت بزنید، UID از سریال.
3. `MASTER_CARD_UID` را تنظیم کنید، `DEBUG_MODE = False`، دوباره فلش.

## ۵. حالت آنلاین

1. کولر در `cooler-web` → `device_id` + `hardware_token`.
2. `config.json`؛ `"online_enabled": true`.
3. آپلود و reset.
4. WSS در داشبورد؛ RFID با WiFi قطع باید کار کند.

## ۶. اعتبارسنجی host (قبل از PR)

```bash
python scripts/validate.py
```

## عیب‌یابی

| علامت | بررسی |
|-------|--------|
| RFID خاموش | فقط 3.3V؛ SPI؛ RST |
| سرعت اشتباه | NC=کند، NO=تند؛ active-low |
| WiFi وصل نمی‌شود | `boot.py` block نمی‌کند |
| رمز SoftAP عجیب | از `local_pin` مشتق |
| Learn cloud را رد می‌کند | عمدی — موتور قفل |

## به‌روزرسانی امن (بدون OTA)

[`docs/OTA.fa.md`](docs/OTA.fa.md) — `mpremote` و نگه‌داشتن کپی سالم قبلی.
