# Hardware bench — step-by-step walkthrough

**Languages:** [English](BENCH_WALKTHROUGH.md) (default) · [Persian](BENCH_WALKTHROUGH.fa.md)

Hands-on guide for **A (physical bench)**. Check off each step; use [HARDWARE_BENCH.md](HARDWARE_BENCH.md) as the pass/fail matrix.

---

## Before you start

| Item | You need |
|------|----------|
| PC | Windows + Python 3.11+ |
| USB | ESP32 data cable (known good COM port) |
| Tools | `pip install mpremote` + `pip install -r requirements-dev.txt` |
| Safety | Mains lockout / qualified person for AC wiring |

```powershell
cd D:\0\RFID-Cooler
python scripts/validate.py
python scripts/run_tests.py
pip install mpremote
pip install -r requirements-dev.txt
```

---

## Phase 1 — Flash & serial (≈15 min)

### 1.1 Find COM port

```powershell
mpremote connect list
# note COM3 (example)
$COM = "COM3"
```

### 1.2 Flash MicroPython (once per board)

Download **ESP32 Generic** `.bin` from [micropython.org](https://micropython.org/download/ESP32_GENERIC/) and flash with esptool if not already installed.

### 1.3 Upload firmware files

**One-liner (recommended):**

```powershell
cd D:\0\RFID-Cooler
.\scripts\flash_device.ps1 -Port COM3
# with bench config for mock backend:
.\scripts\flash_device.ps1 -Port COM3 -IncludeConfig -ConfigPath config.bench.example.json
```

**Manual loop (equivalent):**

```powershell
$COM = "COM3"
$files = @(
  "boot.py","main.py","mfrc522.py",
  "wifi_manager.py","ap_manager.py","local_http.py","dns_captive.py",
  "outbox.py","cloud.py","ws_client.py",
  "wall_inputs.py","rf433.py","ble_control.py","sms_modem.py",
  "mqtt_client.py","ota_stub.py"
)
foreach ($f in $files) {
  python -m mpremote connect $COM fs cp $f ":$f"
}
python -m mpremote connect $COM reset
```

### 1.4 Open serial monitor

```powershell
.\scripts\bench_live.ps1 -Port COM3
# or timed capture + pattern check:
.\scripts\bench_live.ps1 -Port COM3 -Snapshot -SnapshotSeconds 10
```

Legacy:

```powershell
mpremote connect $COM repl
```

**Expect within ~2 s:**

```
[BOOT] RFID-Cooler ready ...
[HW] RFID Initialized & Ready
[SYS] Cloud WSS disabled
[SYS] 0 Cards Loaded.
```

If RFID init fails → check **3.3 V** and SPI wiring (GPIO 5/18/23/19/4).

---

## Phase 2 — Master UID & offline L0 (≈20 min)

### 2.1 Enable DEBUG_MODE once

Edit `main.py` on PC:

```python
DEBUG_MODE = True
```

Re-upload only `main.py`, reset, tap each card on RC522.

**Expect:** `[RFID] Scanned: 0x........`  
Pick master card → set `MASTER_CARD_UID = "0x........"`  
Set `DEBUG_MODE = False` → re-upload `main.py`.

### 2.2 Run L0 tests (no WiFi)

Ensure no `config.json` **or** `"online_enabled": false`.

| Step | You do | Serial / physical |
|------|--------|-------------------|
| L0-1 | Power cycle | Relays click then safe OFF; RFID ready |
| L0-2 | Master short tap ×4 | Off→Slow→Fast→Off + beeps |
| L0-3 | From Off → Slow | 3 s fast kick-start then slow path |
| L0-4 | Tap again during 3 s | `[COOLER] Kick-Start Aborted` |
| L0-5 | Master hold 4 s | `ENTER LEARN MODE` |
| L0-6 | Scan user card ×2 | ADDED then REMOVED |
| L0-7 | Short tap master | `EXIT LEARN MODE` |
| L0-8 | Unknown card | Access Denied beep |

Tick boxes in [HARDWARE_BENCH.md §1](HARDWARE_BENCH.md#1-layer-0--offline-core-no-wifi).

---

## Phase 3 — Dry-switch safety (≈10 min)

**Only if mains is wired and you have a safe observation method (LED on mech coil, sound, or scope).**

| Step | Check |
|------|--------|
| DS-1 | Mechanical **never** clicks while SSR holds load ON |
| DS-2 | Slow steady: SSR ON, mech OFF |
| DS-3 | Fast steady: SSR ON, mech ON |
| DS-4 | Off: both OFF |

If DS-1 fails → **stop** — fix wiring (NC/NO) or firmware before continuing.

---

## Phase 4 — Online with mock backend (≈25 min)

Use this when `door_control` is **not** running. Your PC acts as the cloud.

### 4.1 PC LAN IP

```powershell
ipconfig
# Example: 192.168.1.50
```

### 4.2 Start mock backend (Terminal A)

```powershell
cd D:\0\RFID-Cooler
python scripts/integration/mock_ws_backend.py --interactive --port 8765
```

Leave running. Commands available when device connects: `status`, `set 1`, `cycle`, `open`, `quit`.

### 4.3 Device config (Terminal B)

Create `config.json` from [`config.bench.example.json`](../config.bench.example.json) — set `server_host` to your PC LAN IP:

```json
{
  "wifi_ssid": "YOUR_WIFI",
  "wifi_pass": "YOUR_WIFI_PASS",
  "server_host": "192.168.1.50",
  "server_port": 8765,
  "use_ssl": false,
  "ws_path": "/ws/hardware",
  "hardware_token": "bench-token",
  "device_id": "bench-001",
  "device_role": "cooler",
  "online_enabled": true,
  "outbox_enabled": true,
  "lan_http_enabled": true,
  "local_pin": "1234"
}
```

Upload:

```powershell
mpremote connect $COM fs cp config.json :config.json
mpremote connect $COM reset
```

### 4.4 WSS bench steps

| ID | Terminal A (mock) | Device serial | Pass |
|----|-------------------|---------------|------|
| WSS-1 | see `connect path=...` | `[WS] Connected` | ☐ |
| WSS-2 | `status` | `← status state=…` | ☐ |
| WSS-3 | `set 1` | `ACK accepted` then `applied`; relay slow | ☐ |
| WSS-4 | `set 2` | ACK; fast | ☐ |
| WSS-5 | `set 0` | ACK; off | ☐ |
| WSS-6 | `cycle` | state wraps | ☐ |
| WSS-7 | Enter Learn on device; `set 1` | ACK rejected learn_mode | ☐ |
| WSS-8 | `open` | ACK rejected; no motor | ☐ |

### 4.5 Outbox (WSS-10/11)

1. Stop mock backend (Ctrl+C) or block PC firewall briefly  
2. Tap RFID once (events queue in flash)  
3. Restart mock backend  
4. **Expect:** backlog uplink without extra motor moves  

---

## Phase 5 — Live door_control backend (when available)

### 5.1 Provision in cooler-web

Create customer + cooler → copy `device_id` + `hardware_token`.

### 5.2 config.json

```json
"server_host": "your-server.example.com",
"server_port": 443,
"use_ssl": true,
"online_enabled": true
```

### 5.3 Probe from PC (sanity check server reachable)

```powershell
python scripts/integration/probe_device_session.py `
  --host your-server.example.com --port 443 --use-ssl true `
  --token DEVICE_TOKEN --device-id cooler-001 `
  --send-get-status
```

Note: probe opens a **second** WS client — some backends allow only one hardware session. Prefer dashboard commands when device is already online.

### 5.4 Dashboard WSS tests

Repeat WSS-1…WSS-11 from [HARDWARE_BENCH.md §3](HARDWARE_BENCH.md#3-online-dual-mode-backend-required) using cooler-web UI instead of mock `set` commands.

---

## Phase 6 — Optional edge channels

Only if wired and enabled in `config.json`:

| Channel | Quick smoke |
|---------|-------------|
| SoftAP | Join `Cooler-*` AP; PIN = `local_pin` repeated (1234→12341234) |
| LAN HTTP | `http://<STA-IP>/` → Off/Slow/Fast |
| Wall | Toggle dry-contact inputs |
| RF433 | POST `/api/rf433/learn` + remote |

---

## Phase 7 — Sign-off

Copy the table from [HARDWARE_BENCH.md §6](HARDWARE_BENCH.md#6-sign-off-record) into your lab notebook with date, git hash, and operator name.

```powershell
git rev-parse --short HEAD
python scripts/validate.py
python scripts/run_tests.py
python scripts/integration/run_integration.py
```

---

## Troubleshooting

| Symptom | Likely cause | Fix |
|---------|--------------|-----|
| No `[WS] Connected` | Wrong IP/port; SSL mismatch | `use_ssl: false` for mock; same LAN |
| RFID silent | 3.3 V / SPI | Re-seat RC522; check RST GPIO 4 |
| ACK never `applied` | Learn mode; bad mode | Exit learn; mode 0–2 only |
| Mech clicks under load | Wiring | SSR must drop before mech moves |
| `mpremote` busy | REPL open elsewhere | Close other serial tools |

---

**Next:** [INTEGRATION.md](INTEGRATION.md) (automation scripts) · [HARDWARE_BENCH.fa.md](BENCH_WALKTHROUGH.fa.md)
