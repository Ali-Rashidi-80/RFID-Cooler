# Resilience product roadmap — multi-tenant RFID cooler (Iran)

Needs analysis and Must / Should / Optional features based on ThingsBoard, ESPHome/local-first, Iran industrial control patterns (SMS/BLE), and national network constraints.

## Core product architecture

```
Layer 0 — always: RFID + dry relay + Learn (+ optional wall dry-contact)
Layer 1 — LAN: SoftAP/Captive + local web on AP and STA IP
Layer 1b — RF433 learn: Iran market physical remotes (no internet)
Layer 2 — BLE: near control with app/Flutter without internet
Layer 3 — SMS/GSM: remote command when data is down
Layer 4 — Cloud WSS: multi-customer dashboard (MQTT optional R3)
Optional companion — market smart plug ON/OFF for whole supply only (not 3-speed)
```

**Golden rule:** losing any upper layer never disables lower layers.

---

## Gap vs ThingsBoard (goal: complete for this domain)

| ThingsBoard capability | Our status | Cooler product priority |
|------------------------|------------|-------------------------|
| Device registry + credentials | Yes (per-device token) | Keep |
| Telemetry + dashboards | Partial (WS status + Next.js) | P1 expand |
| Bidirectional RPC | SET_MODE/CYCLE | P0 keep + ACK |
| Rule engine / alarms | No | P1 (temp, offline, usage) |
| Local buffer when offline | Yes (`outbox.py` / `outbox.jsonl`) | Keep |
| Gateway + MQTT | Optional R3 (`mqtt_client.py`) | Optional |
| Multi-tenant | Yes | Keep + harden |
| OTA | Stub (`ota_stub.py` + `docs/OTA.md`) | P2 after stability |
| Offline edge UX | SoftAP/HTTP/wall/RF/BLE/SMS (code); Flutter field BLE+LAN | Keep + hardware bench |
| SMS in Iran | Melipayamak cloud alerts + SIM800 command (SKU) | Keep |
| Network mirrors | cooler-web + Chabokan npm/pip/docker | Keep |

We should not clone all of ThingsBoard; we must lead in **evaporative cooler control + multi-tenant + Iran resilience**: real local-first, SMS/BLE, Persian/Flutter UX.

---

## Control channels — Iran market triage

Research: Digikala Mag smart cooler keys; Tuya/Sonoff/Asane/Jaban/Lexite (WiFi+RF); 433 plugs; Nest/plug limits for inductive motors.

### Must

1. **Local RFID** (shipped)
2. **Multi-tenant Cloud WSS** (shipped) + **ACK/outbox** (shipped)
3. **SoftAP + Captive + local web (PIN)** (shipped)
4. **HTTP on STA IP (LAN)** when home WiFi up (shipped)
5. **RF433 learn** — `/api/rf433/learn` + button map (shipped; best-effort)
6. **Melipayamak offline-device alerts** (backend `cooler_alerts`)

### Should

7. **Wall dry-contact** parallel Off/Slow/Fast (**R1 optional** `wall_enabled`)
8. **BLE GATT + PIN** + Flutter sketch (**R2**)
9. **SIM800 SMS command** (separate SKU — **R2**)
10. **Audit with channel** (**R1 start**, complete per channel)

### Optional

11. **Market plug/relay whole-supply ON/OFF only** — not 3-speed
12. Cloud schedules, optional MQTT, Flutter field BLE+LAN; **thermostat + real OTA still deferred** (`temp_enabled` no sensor; `ota_stub`)

### Reject

- Home smart plug as primary Slow/Fast motor control (inductive load + single relay)
- Nest/24V thermostat direct on motor
- Mandatory Tuya/eWeLink cloud dependency
- Zigbee as primary Iran channel (cooler key market = WiFi+RF)

### Smart plug stance

Market 433 plugs suit pump/lighting; for 3-speed coolers they are **not core**. Same market UX via **433 learn on our controller** + dry-switch core.

---

## Product feature matrix

### P0 — production / bulletproof

| Feature | Why |
|---------|-----|
| Local command + telemetry flash queue | Like TB Gateway event storage |
| ACK for SET_MODE (accepted/applied/rejected) | Prevent lying UI |
| AP + local web + LAN HTTP on STA | No internet; home control without cloud |
| Chabokan mirror first for npm/pip/docker | National network |
| Channel watchdog + reconnect + offline fanout | User trust (dual-mode debt) |
| Melipayamak device-offline alert | When server has internet |
| Command audit log (who/where/channel) | B2B legal |

### P1 — competitive / platform (R2)

| Feature | Why |
|---------|-----|
| RF433 learn market remote | Iran Tuya/Sonoff WiFi+RF pattern |
| Wall dry-contact | Keep traditional UX |
| BLE near control + PIN | Workshop without WiFi |
| SIM800 SMS command | Data down; antenna up |
| Flutter BLE/LAN sketch | Field mobile |
| Temp alarm / schedules | Digikala/Tuya need |
| Usage/event export | B2B |

### P2 — optional / next phase

| Feature | Why |
|---------|-----|
| MQTT + retain | IoT / HA standard |
| Secure OTA + rollback | Fleet ops |
| Full Flutter Cloud\|LAN\|BLE | Complement Next.js |
| SKU Lite plug/contactor ON/OFF | Supply companion; not 3-speed |
| Energy meter / CT clamp | Differentiation |
| Simple rules (if temp>X → fast) | Near TB without full engine |

---

## User research summary

1. **Internet outage must not leave cooler uncontrollable** (local-first; WiFi-only market models weak).
2. **Simple physical remote without phone** (Iran 433 — SKC / Sonoff-Tuya companion).
3. **Traditional wall switch must still work** (parallel dry-contact).
4. **On-before-arrival + timer/temp** (common Digikala/app ask).
5. **Multi customer / multi device** with isolation (B2B SaaS).
6. **Easy install without laptop** → Captive Portal.
7. **Dependencies from inside country** → Chabokan first.
8. **Status transparency** online/offline + command ACK.
9. **Motor safety** dry-switch; reject single-relay 3-speed.

---

## Implementation phasing

### Phase R1 — Local edge + dual-mode debt

1. Captive portal + AP web + LAN HTTP on STA  
2. Outbox + ACK; optional wall inputs  
3. cooler-web reconnect + offline fanout  
4. Melipayamak alerts; Chabokan mirrors  

### Phase R2 — RF433 + near-field + SMS

1. RF433 learn market remote  
2. BLE + Flutter BLE/LAN sketch  
3. SIM800 command (separate SKU)  

### Phase R3 — Optional platform parity

1. MQTT / schedules / thermostat  
2. OTA; full Flutter  
3. SKU Lite plug+contactor ON/OFF docs  

---

## Success criteria (per phase)

- **After R1:** RFID + AP/LAN web (+ wall); ACK/outbox; immediate offline in UI; Chabokan build  
- **After R2:** + RF433 + BLE + SMS UART  
- **Final product:** Must+Should subset; dry-switch untouched; plug optional supply only  

---

*Audit pass 3 final 2026-07-20 — sealed plan for execution. Sources: ThingsBoard Gateway, MicroPython captive/aioble, ESPHome local-first, Digikala Mag cooler keys, Tuya/Sonoff WiFi+RF, iran.chabokan.net / mirror2.*

**Languages:** [English](PRODUCT_ROADMAP_RESILIENCE.md) · [Persian](PRODUCT_ROADMAP_RESILIENCE.fa.md)
