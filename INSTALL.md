# Install & deploy

**Languages:** [English](INSTALL.md) (default) · [Persian](INSTALL.fa.md)

## Prerequisites

| Tool | Purpose |
|------|---------|
| [MicroPython ESP32 firmware](https://micropython.org/download/ESP32_GENERIC/) | Device runtime |
| [`mpremote`](https://docs.micropython.org/en/latest/reference/mpremote.html) | Copy files + reset |
| USB serial driver | ESP32 dev board |

In Iran, prefer Chabokan mirrors for host Python/npm when building the dashboard — see [`docs/IRAN_MIRRORS.md`](docs/IRAN_MIRRORS.md).

## 1. Flash MicroPython

1. Hold BOOT if needed; erase flash once on a new board.
2. Flash the current stable ESP32 Generic MicroPython `.bin`.
3. Confirm REPL: `mpremote connect COM3 repl` (adjust port).

## 2. Upload firmware files

From the repo root (Windows example):

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

## 3. Configuration

```powershell
copy config.example.json config.json
# Edit config.json locally — never commit
mpremote connect COM3 fs cp config.json :config.json
```

For **offline-only**, omit `config.json` or set `"online_enabled": false`.

## 4. Master card UID

1. Set `DEBUG_MODE = True` in `main.py` once.
2. Flash `main.py`, tap cards, read UID from serial.
3. Set `MASTER_CARD_UID`, set `DEBUG_MODE = False`, re-flash.

## 5. Online mode

1. Provision cooler in `cooler-web` dashboard → copy `device_id` + `hardware_token`.
2. Fill `config.json`; set `"online_enabled": true`.
3. Upload `config.json` and reset.
4. Verify WSS status in dashboard; RFID must still work with WiFi disabled.

## 6. Validate on host (before PR)

```bash
python scripts/validate.py
```

## Troubleshooting

| Symptom | Check |
|---------|--------|
| RFID silent | 3.3 V only; SPI wiring; RST pulse |
| Motor wrong speed | NC=slow, NO=fast; active-low |
| WiFi never connects | `boot.py` non-blocking — STA starts in `main.py` |
| SoftAP password odd | Derived from `local_pin` (repeated to ≥8 chars) |
| Learn Mode rejects cloud | By design — motor locked |

## Safe update (no OTA yet)

See [`docs/OTA.md`](docs/OTA.md) — copy `.py` via `mpremote`, keep previous known-good copy.
