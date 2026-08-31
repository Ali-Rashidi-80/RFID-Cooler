# Integration testing (backend & automation)

**Languages:** [English](INTEGRATION.md) (default) · [Persian](INTEGRATION.fa.md)

Scripts under `scripts/integration/` — **host PC only**, not flashed to ESP32.

---

## Install

```bash
pip install -r requirements-dev.txt
```

Optional env vars for live probe:

| Variable | Example |
|----------|---------|
| `WS_HOST` | `your-server.example.com` |
| `WS_PORT` | `443` |
| `WS_USE_SSL` | `true` |
| `WS_TOKEN` | device hardware token |
| `WS_DEVICE_ID` | `cooler-001` |

---

## Script reference

| Script | Purpose |
|--------|---------|
| [`run_integration.py`](../scripts/integration/run_integration.py) | **CI-style** E2E: dashboard WS → CloudBridge → ACK accepted→applied (no ESP32) |
| [`mock_ws_backend.py`](../scripts/integration/mock_ws_backend.py) | **Bench** mock cloud; ESP32 connects here; `--interactive` stdin commands |
| [`probe_device_session.py`](../scripts/integration/probe_device_session.py) | **Probe** live or mock server; send GET_STATUS / SET_MODE / CYCLE / OPEN |

---

## 1. Automated integration (no hardware)

```bash
python scripts/integration/run_integration.py
```

Exit 0 = CloudBridge honors backend ACK contract through a real WebSocket framing layer.

Run in CI after host unit tests:

```bash
python scripts/run_tests.py
python scripts/integration/run_integration.py
```

---

## 2. Mock backend + physical ESP32

**Terminal A:**

```bash
python scripts/integration/mock_ws_backend.py --interactive --host 0.0.0.0 --port 8765
```

**Device `config.json`:**

```json
{
  "server_host": "<PC-LAN-IP>",
  "server_port": 8765,
  "use_ssl": false,
  "ws_path": "/ws/hardware",
  "hardware_token": "bench-token",
  "device_id": "bench-001",
  "device_role": "cooler",
  "online_enabled": true,
  "wifi_ssid": "...",
  "wifi_pass": "..."
}
```

**Interactive commands:** `status`, `set 0`, `set 1`, `set 2`, `cycle`, `open`, `quit`

Full walkthrough: [BENCH_WALKTHROUGH.md](BENCH_WALKTHROUGH.md)

---

## 3. Probe live door_control

When backend is deployed and (optionally) device already online:

```bash
python scripts/integration/probe_device_session.py \
  --host your-server.example.com \
  --port 443 \
  --use-ssl true \
  --token DEVICE_TOKEN \
  --device-id cooler-001 \
  --send-set-mode 1 \
  --expect-ack applied
```

**Honest limits:**

- Some backends allow **one** hardware WebSocket per token — probing may conflict with a connected device.
- Prefer cooler-web dashboard for WSS-3…WSS-8 when device is live.
- Probe is best for **server reachability** and **protocol smoke** on staging.

---

## Protocol contract (reference)

Downlink (server → device):

```json
{"cmd":"SET_MODE","mode":1,"command_id":"uuid"}
{"cmd":"CYCLE","command_id":"uuid"}
{"cmd":"GET_STATUS"}
{"cmd":"OPEN","command_id":"uuid"}
```

Uplink ACK (device → server):

```json
{"type":"ACK","command_id":"uuid","cmd":"SET_MODE","status":"accepted|applied|rejected","reason":"...","mode":1}
```

See [README — Dual-mode protocol](../README.md#dual-mode-protocol).

---

## Troubleshooting

| Issue | Fix |
|-------|-----|
| `ModuleNotFoundError: websockets` | `pip install -r requirements-dev.txt` |
| Device never connects | Same WiFi/LAN; disable SSL for mock; check firewall on port 8765 |
| No ACK in probe | Device not connected; backend routes elsewhere |
| `run_integration` fails | Run from repo root; check `cloud.py` unchanged |
