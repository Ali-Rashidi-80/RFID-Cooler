#!/usr/bin/env python3
"""
Mock WebSocket backend for ESP32 bench + optional interactive downlink.

Terminal 1 (mock backend — device connects here):
  pip install -r requirements-dev.txt
  python scripts/integration/mock_ws_backend.py --interactive

Terminal 2 (flash config pointing at this PC LAN IP, port 8765, use_ssl false)

Interactive commands (Terminal 1 while device connected):
  status          send GET_STATUS
  set 0|1|2       SET_MODE
  cycle           CYCLE
  open            OPEN (door — expect reject on cooler)
  quit
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
import uuid
from typing import Any

try:
    import websockets
    from websockets.asyncio.server import serve
except ImportError:
    print("Install: pip install -r requirements-dev.txt", file=sys.stderr)
    sys.exit(1)

_device_ws: Any = None
_state: dict[str, Any] = {"cooler_state": 0, "learn_mode": False, "uplinks": []}


def _record(msg: dict) -> None:
    _state["uplinks"].append(msg)
    if len(_state["uplinks"]) > 200:
        _state["uplinks"] = _state["uplinks"][-100:]
    if msg.get("type") == "status":
        _state["cooler_state"] = msg.get("cooler_state", 0)
        _state["learn_mode"] = bool(msg.get("learn_mode", False))


async def _send_downlink(cmd: str, mode: int | None = None) -> None:
    global _device_ws
    if _device_ws is None:
        print("[MOCK-WS] no device connected")
        return
    cid = str(uuid.uuid4())
    payload: dict = {"cmd": cmd, "command_id": cid}
    if cmd == "SET_MODE":
        payload["mode"] = int(mode)
    await _device_ws.send(json.dumps(payload))
    print("[MOCK-WS] downlink →", payload)


async def _handler(websocket):
    global _device_ws
    path = getattr(getattr(websocket, "request", None), "path", "") or ""
    print(f"[MOCK-WS] connect path={path}")
    _device_ws = websocket
    try:
        async for raw in websocket:
            try:
                msg = json.loads(raw)
            except json.JSONDecodeError:
                print("[MOCK-WS] raw:", raw[:120])
                continue
            _record(msg)
            t = msg.get("type")
            if t == "ping":
                print("[MOCK-WS] ← ping")
            elif t == "status":
                print(
                    "[MOCK-WS] ← status state=%s learn=%s"
                    % (msg.get("cooler_state"), msg.get("learn_mode"))
                )
            elif t == "ACK":
                print(
                    "[MOCK-WS] ← ACK %s %s %s"
                    % (msg.get("cmd"), msg.get("status"), msg.get("reason"))
                )
            elif t == "scan":
                print("[MOCK-WS] ← scan", msg.get("action"), msg.get("rfid"))
            else:
                print("[MOCK-WS] ←", msg)
    except websockets.ConnectionClosed:
        pass
    finally:
        if _device_ws is websocket:
            _device_ws = None
        print("[MOCK-WS] device disconnected")


async def _interactive_loop() -> None:
    print("[MOCK-WS] Interactive: status | set 0|1|2 | cycle | open | quit")
    loop = asyncio.get_event_loop()
    while True:
        line = await loop.run_in_executor(None, lambda: input("mock> ").strip())
        if not line:
            continue
        if line in ("q", "quit", "exit"):
            return
        if line == "status":
            await _send_downlink("GET_STATUS")
        elif line == "cycle":
            await _send_downlink("CYCLE")
        elif line == "open":
            await _send_downlink("OPEN")
        elif line.startswith("set "):
            try:
                mode = int(line.split()[1])
            except (IndexError, ValueError):
                print("usage: set 0|1|2")
                continue
            await _send_downlink("SET_MODE", mode)
        else:
            print("unknown:", line)


async def run_server(host: str, port: int, interactive: bool) -> None:
    print(f"[MOCK-WS] ws://{host}:{port}/ws/hardware?token=TOKEN&role=cooler&device_id=ID")
    async with serve(_handler, host, port):
        if interactive:
            await _interactive_loop()
        else:
            await asyncio.Future()


def main() -> int:
    p = argparse.ArgumentParser(description="Mock cooler WebSocket backend")
    p.add_argument("--host", default="0.0.0.0")
    p.add_argument("--port", type=int, default=8765)
    p.add_argument(
        "--interactive",
        action="store_true",
        help="stdin commands to connected device (bench mode)",
    )
    args = p.parse_args()
    try:
        asyncio.run(run_server(args.host, args.port, args.interactive))
    except KeyboardInterrupt:
        print("\n[MOCK-WS] stopped")
    return 0


if __name__ == "__main__":
    sys.exit(main())
