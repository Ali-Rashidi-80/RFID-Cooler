#!/usr/bin/env python3
"""
End-to-end integration: WebSocket wire format + CloudBridge ACK contract.

No ESP32. Dashboard client connects → device handler (CloudBridge) → ACK uplink.

  pip install -r requirements-dev.txt
  python scripts/integration/run_integration.py
"""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HOST_TEST = ROOT / "test" / "host"
sys.path.insert(0, str(HOST_TEST))
sys.path.insert(0, str(ROOT))

from _mpy_stubs import install

install()

from cloud import CloudBridge

try:
    import websockets
    from websockets.asyncio.server import serve
except ImportError:
    print("Install: pip install -r requirements-dev.txt", file=sys.stderr)
    sys.exit(1)


class MockHW:
    def __init__(self):
        self.current_task = None
        self.modes: list[int] = []

    def change_mode(self, mode):
        self.modes.append(int(mode))
        self.current_task = None

    async def beep_cooler_slow(self):
        pass

    async def beep_cooler_fast(self):
        pass

    async def beep_cooler_off(self):
        pass

    async def beep_denied(self):
        pass


async def run_e2e() -> int:
    async def device_handler(websocket):
        hw = MockHW()
        st = {"v": 0, "learn": False}
        bridge = CloudBridge(
            hw,
            lambda: st["v"],
            lambda v: st.update(v=int(v)),
            lambda: st["learn"],
        )

        class WSAdapter:
            open = True

            async def send_json(self, obj):
                await websocket.send(json.dumps(obj))
                return True

        bridge.attach_ws(WSAdapter(), "bench-001", "cooler")

        async for raw in websocket:
            await bridge.handle_command(raw)

    async with serve(device_handler, "127.0.0.1", 0) as server:
        port = server.sockets[0].getsockname()[1]
        url = f"ws://127.0.0.1:{port}/"

        async with websockets.connect(url) as dashboard:
            await dashboard.send(
                json.dumps(
                    {"cmd": "SET_MODE", "mode": 2, "command_id": "e2e-001"}
                )
            )
            acks = []
            deadline = asyncio.get_event_loop().time() + 3.0
            while asyncio.get_event_loop().time() < deadline:
                try:
                    raw = await asyncio.wait_for(dashboard.recv(), timeout=0.5)
                    msg = json.loads(raw)
                    if msg.get("type") == "ACK":
                        acks.append(msg)
                        if len(acks) >= 2:
                            break
                except asyncio.TimeoutError:
                    continue

    statuses = [a.get("status") for a in acks if a.get("command_id") == "e2e-001"]
    if statuses != ["accepted", "applied"]:
        print("INTEGRATION FAILED: expected accepted→applied, got", statuses)
        return 1

    print("INTEGRATION OK -- WebSocket SET_MODE -> ACK accepted->applied")
    return 0


def main() -> int:
    return asyncio.run(run_e2e())


if __name__ == "__main__":
    sys.exit(main())
