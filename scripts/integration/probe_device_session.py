#!/usr/bin/env python3
"""
Interactive WebSocket client — probes a live or mock cooler backend session.

Simulates what cooler-web / door_control sends downlink and prints uplink.

Usage (mock backend on same PC):
  # Terminal 1
  python scripts/integration/mock_ws_backend.py

  # Terminal 2 — connect as if we were the dashboard command path
  python scripts/integration/probe_device_session.py \\
      --host 127.0.0.1 --port 8765 --use-ssl false \\
      --token test-token --device-id bench-001 \\
      --send-set-mode 1 --expect-ack applied

Live door_control (TLS):
  python scripts/integration/probe_device_session.py \\
      --host your-server.example.com --port 443 --use-ssl true \\
      --token DEVICE_TOKEN --device-id cooler-001 \\
      --send-get-status

Environment overrides: WS_HOST, WS_PORT, WS_TOKEN, WS_DEVICE_ID, WS_USE_SSL
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
import uuid

try:
    import websockets
except ImportError:
    print("Install: pip install -r requirements-dev.txt", file=sys.stderr)
    sys.exit(1)


def build_url(host: str, port: int, use_ssl: bool, ws_path: str, token: str, role: str, device_id: str) -> str:
    scheme = "wss" if use_ssl else "ws"
    sep = "&" if "?" in ws_path else "?"
    path = f"{ws_path}{sep}token={token}&role={role}&device_id={device_id}"
    if not path.startswith("/"):
        path = "/" + path
    default_port = 443 if use_ssl else 80
    if (use_ssl and port == 443) or (not use_ssl and port == 80):
        return f"{scheme}://{host}{path}"
    return f"{scheme}://{host}:{port}{path}"


async def probe(
    url: str,
    *,
    send_set_mode: int | None,
    send_cycle: bool,
    send_open: bool,
    send_get_status: bool,
    expect_ack: str | None,
    timeout_s: float,
) -> int:
    errors: list[str] = []
    acks: list[dict] = []
    statuses: list[dict] = []

    async with websockets.connect(url, open_timeout=timeout_s) as ws:
        print("[PROBE] Connected", url)

        async def drain(seconds: float):
            end = asyncio.get_event_loop().time() + seconds
            while asyncio.get_event_loop().time() < end:
                try:
                    raw = await asyncio.wait_for(ws.recv(), timeout=0.5)
                except asyncio.TimeoutError:
                    continue
                try:
                    msg = json.loads(raw)
                except json.JSONDecodeError:
                    print("[PROBE] non-JSON:", raw[:200])
                    continue
                t = msg.get("type")
                if t == "status":
                    statuses.append(msg)
                    print("[PROBE] uplink status", msg)
                elif t == "ACK":
                    acks.append(msg)
                    print("[PROBE] uplink ACK", msg)
                elif t == "ping":
                    print("[PROBE] uplink ping")
                elif t == "scan":
                    print("[PROBE] uplink scan", msg)
                else:
                    print("[PROBE] uplink", msg)

        # Initial drain — device may push status on connect
        await drain(2.0)

        async def send_cmd(cmd: str, mode: int | None = None) -> str:
            cid = str(uuid.uuid4())
            payload: dict = {"cmd": cmd, "command_id": cid}
            if cmd == "SET_MODE":
                payload["mode"] = int(mode)
            await ws.send(json.dumps(payload))
            print("[PROBE] downlink", payload)
            return cid

        expected_ids: list[str] = []

        if send_get_status:
            cid = await send_cmd("GET_STATUS")
            expected_ids.append(cid)

        if send_set_mode is not None:
            cid = await send_cmd("SET_MODE", send_set_mode)
            expected_ids.append(cid)

        if send_cycle:
            cid = await send_cmd("CYCLE")
            expected_ids.append(cid)

        if send_open:
            cid = await send_cmd("OPEN")
            expected_ids.append(cid)

        await drain(5.0)

    if expect_ack:
        matching = [a for a in acks if a.get("status") == expect_ack]
        if not matching:
            errors.append(f"no ACK with status={expect_ack!r}; got {[a.get('status') for a in acks]}")

    if send_set_mode is not None and expect_ack == "applied":
        applied = [a for a in acks if a.get("status") == "applied" and a.get("cmd") in ("SET_MODE", "CYCLE")]
        if applied and applied[-1].get("mode") != send_set_mode:
            errors.append(
                f"applied mode {applied[-1].get('mode')} != requested {send_set_mode}"
            )

    if errors:
        print("[PROBE] FAILED:")
        for e in errors:
            print("  -", e)
        return 1

    print(f"[PROBE] OK — {len(acks)} ACK(s), {len(statuses)} status(es)")
    return 0


def main() -> int:
    p = argparse.ArgumentParser(description="Probe cooler WebSocket backend/session")
    p.add_argument("--host", default=os.environ.get("WS_HOST", "127.0.0.1"))
    p.add_argument("--port", type=int, default=int(os.environ.get("WS_PORT", "8765")))
    p.add_argument("--use-ssl", choices=("true", "false"), default=os.environ.get("WS_USE_SSL", "false"))
    p.add_argument("--ws-path", default="/ws/hardware")
    p.add_argument("--token", default=os.environ.get("WS_TOKEN", "test-token"))
    p.add_argument("--device-id", default=os.environ.get("WS_DEVICE_ID", "bench-001"))
    p.add_argument("--role", default="cooler")
    p.add_argument("--send-set-mode", type=int, default=None, metavar="0|1|2")
    p.add_argument("--send-cycle", action="store_true")
    p.add_argument("--send-open", action="store_true")
    p.add_argument("--send-get-status", action="store_true")
    p.add_argument("--expect-ack", choices=("accepted", "applied", "rejected"), default=None)
    p.add_argument("--timeout", type=float, default=10.0)
    args = p.parse_args()

    if not any([args.send_set_mode is not None, args.send_cycle, args.send_open, args.send_get_status]):
        args.send_get_status = True

    url = build_url(
        args.host,
        args.port,
        args.use_ssl == "true",
        args.ws_path,
        args.token,
        args.role,
        args.device_id,
    )

    try:
        return asyncio.run(
            probe(
                url,
                send_set_mode=args.send_set_mode,
                send_cycle=args.send_cycle,
                send_open=args.send_open,
                send_get_status=args.send_get_status,
                expect_ack=args.expect_ack,
                timeout_s=args.timeout,
            )
        )
    except Exception as exc:
        print("[PROBE] ERROR:", exc)
        return 1


if __name__ == "__main__":
    sys.exit(main())
