# Hardware & backend integration bench

**Languages:** [English](HARDWARE_BENCH.md) (default) · [Persian](HARDWARE_BENCH.fa.md)

Use this checklist on a **real ESP32 + RC522 + SSR + mechanical SPDT** setup connected to your `door_control` backend when available.  
Host CI (`scripts/validate.py`, `scripts/run_tests.py`) proves protocol contracts only — **this bench proves physics and fleet UX**.

Record results in the table at the bottom. Do not skip safety steps.

---

## 0. Pre-flight (mandatory)

| Step | Action | Pass criteria |
|------|--------|---------------|
| 0.1 | **Cut mains** before any wiring change | Breaker off, verified dead |
| 0.2 | Verify **NC → Slow**, **NO → Fast**, SSR → pump phase + mech COM | Matches [README](../README.md#hardware) |
| 0.3 | RC522 on **3.3 V only**; SPI pins 5/18/23/19/4 | REPL boot, no brownout |
| 0.4 | Flash MicroPython + all firmware `.py` files | [`INSTALL.md`](../INSTALL.md) |
| 0.5 | Copy `config.example.json` → `config.json` on device | Never commit secrets |
| 0.6 | Set `MASTER_CARD_UID` (one `DEBUG_MODE` session) | Serial prints UID once |
| 0.7 | Serial log ready (`mpremote connect COMx repl` or UART) | Timestamp + grep-friendly |

**Abort if:** mechanical relay clicks while SSR is ON (load switching) — wiring or firmware regression.

---

## 1. Layer 0 — offline core (no WiFi)

Set `"online_enabled": false` or omit WiFi keys. **Do not connect WiFi.**

| ID | Test | Steps | Expected |
|----|------|-------|----------|
| L0-1 | Cold boot | Power on, no `config.json` WiFi | RFID loop starts ≤2 s; relays safe OFF |
| L0-2 | Master short tap | Tap master, release <4 s | Off→Slow→Fast→Off cycle; correct beeps |
| L0-3 | Kick-start | Enter Slow from Off | 3 s Fast audible/physical, then dry-switch to Slow |
| L0-4 | Kick-start abort | Tap again during 3 s kick-start | `force_off`; no welded path; safe OFF |
| L0-5 | Learn enter | Master hold 4 s | Motor OFF; learn melody; Learn Mode true |
| L0-6 | Learn add/remove | Scan user card twice in Learn | `cards.json` updated; tmp→rename survives power cut mid-save |
| L0-7 | Learn exit | Master short tap OR 15 s timeout | Learn false; motor stays OFF until next command |
| L0-8 | Denied card | Unknown card outside Learn | Deny beep; no relay motion |
| L0-9 | Rapid tap | 3+ quick taps authorized card | No stuck task; final state consistent |

---

## 2. Dry-switch invariants (safety)

| ID | Test | How to observe | Expected |
|----|------|----------------|----------|
| DS-1 | SSR off before mech move | Scope or LED on mech coil | Mech energizes only when SSR de-energized |
| DS-2 | Slow path | Slow steady state | SSR ON, mech OFF (NC path) |
| DS-3 | Fast path | Fast steady state | SSR ON, mech ON (NO path) |
| DS-4 | Off path | Off | SSR OFF, mech OFF |
| DS-5 | Power loss mid-sequence | Pull USB/mains during kick-start | On reboot: OFF or recoverable; no ambiguous both-path ON |

---

## 3. Online dual-mode (backend required)

Prerequisites:

1. Customer + cooler in `cooler-web` with `device_id` + `hardware_token`
2. `config.json`: `"online_enabled": true`, valid `wifi_*`, `server_*`, token
3. Backend WebSocket route: `/ws/hardware?token=…&role=cooler&device_id=…`

| ID | Test | Steps | Expected |
|----|------|-------|----------|
| WSS-1 | Connect | Boot with WiFi | Serial `[WS] Connected`; dashboard shows online |
| WSS-2 | Status uplink | Open dashboard cooler detail | `cooler_state`, `learn_mode` match device |
| WSS-3 | SET_MODE Slow | Dashboard → Slow | ACK `accepted` then `applied`; motor Slow; kick-start if from Off |
| WSS-4 | SET_MODE Fast | Dashboard → Fast | ACK sequence; motor Fast |
| WSS-5 | SET_MODE Off | Dashboard → Off | ACK; motor Off |
| WSS-6 | CYCLE | Dashboard cycle | ACK; state wraps 0→1→2→0 |
| WSS-7 | Learn reject | Enter Learn on device; SET_MODE from dashboard | ACK `rejected`, reason `learn_mode`; motor stays OFF |
| WSS-8 | OPEN ignored | Send door `OPEN` downlink (if test harness) | No motor motion; ACK `rejected` / denied |
| WSS-9 | RFID wins offline | Disconnect WiFi mid-run | Motor keeps state; RFID still cycles |
| WSS-10 | Reconnect | Restore WiFi | Auto reconnect; status + outbox drain |
| WSS-11 | Outbox | Queue events with WiFi down, then up | Dashboard receives backlog; no duplicate motor moves |

**Backend contract reference:** [README — Dual-mode protocol](../README.md#dual-mode-protocol)

---

## 4. Local edge (optional channels)

Enable only what you wired. PIN = `local_pin` unless noted.

### 4a. SoftAP + captive (`ap_enabled` or no `wifi_ssid`)

| ID | Test | Expected |
|----|------|----------|
| AP-1 | SoftAP visible | SSID `Cooler-<device_id suffix>`; PSK = `local_pin` repeated to ≥8 chars |
| AP-2 | Captive portal | Phone joins AP → local HTML |
| AP-3 | PIN gate | Wrong PIN → 401; correct → mode change |

### 4b. LAN HTTP (`lan_http_enabled`)

| ID | Test | Expected |
|----|------|----------|
| LAN-1 | `GET /api/status` on STA IP | JSON `mode`, `learn_mode`, `channel` |
| LAN-2 | `POST /api/command` SET_MODE | 200 + mode applied; wrong PIN → 401 |
| LAN-3 | WiFi save | Portal save SSID → reconnect; STA preferred over AP when connected |

### 4c. Wall dry-contact (`wall_enabled`)

| ID | Test | Expected |
|----|------|----------|
| WALL-1 | Off / Slow / Fast inputs | Each input selects mode; debounce ≥200 ms |
| WALL-2 | Learn Mode | Wall ignored or rejected (motor locked) — document observed behavior |

### 4d. RF433 (`rf433_enabled`)

| ID | Test | Expected |
|----|------|----------|
| RF-1 | Learn slot | `POST /api/rf433/learn` + remote press | Code stored in `rf_codes.json` |
| RF-2 | Trigger | Press learned button | Matching mode / cycle |

### 4e. BLE / SMS / MQTT (if enabled)

| Channel | Smoke test |
|---------|------------|
| BLE | Connect GATT; PIN JSON `SET_MODE` / `CYCLE` |
| SMS | `COOLER <sms_pin> SLOW` from authorized SIM |
| MQTT | Publish `cmd` retain; status topic updates |

---

## 5. Failure & regression matrix

| ID | Scenario | Expected |
|----|----------|----------|
| F-1 | WiFi drop during SET_MODE kick-start | Local sequence completes or safe abort; no cloud deadlock |
| F-2 | Bad token | WS handshake fail; device stays offline-first; RFID OK |
| F-3 | `cards.tmp` only after power cut during save | Next boot loads cards from tmp |
| F-4 | Watchdog | No permanent hang >10 s without RFID poll (WDT fed in loop) |
| F-5 | Door regression | `OPEN` never energizes cooler relays |

---

## 6. Sign-off record

| Date | Operator | Firmware git/ref | Backend ref | L0 | DS | WSS | Edge | Notes |
|------|----------|------------------|-------------|----|----|-----|------|-------|
| | | | | ☐ | ☐ | ☐ | ☐ | |

**Definition of done (production bench):** L0 + DS all pass; WSS-1…WSS-11 pass if fleet online; edge sections pass for enabled channels; F-1…F-5 pass.

---

## Quick commands

```bash
# Host gates (before field trip)
python scripts/validate.py
python scripts/run_tests.py

# Flash + monitor (adjust COM port)
mpremote connect COM3 fs cp main.py :main.py
mpremote connect COM3 reset
mpremote connect COM3 repl
```

---

*Honest scope: passing host tests + this bench together cover firmware logic and backend contract; mains safety remains operator responsibility.*
