# Cloud command mapping for cooler dual-mode (+ ACK + outbox)
import uasyncio as asyncio
import json
import time


class CloudBridge:
    def __init__(self, hw, get_state, set_state, get_learn, outbox=None):
        self.hw = hw
        self.get_state = get_state
        self.set_state = set_state
        self.get_learn = get_learn
        self.outbox = outbox
        self.ws = None
        self.device_id = ""
        self.device_role = "cooler"

    def attach_ws(self, ws, device_id, device_role="cooler"):
        self.ws = ws
        self.device_id = device_id or ""
        self.device_role = device_role or "cooler"

    def status_payload(self):
        return {
            "type": "status",
            "device_role": self.device_role,
            "device_id": self.device_id,
            "cooler_state": self.get_state(),
            "learn_mode": bool(self.get_learn()),
        }

    async def _send_or_queue(self, payload):
        if self.ws and self.ws.open:
            try:
                await self.ws.send_json(payload)
                return True
            except Exception as e:
                print("[CLOUD] send failed:", e)
        if self.outbox:
            self.outbox.append(payload)
        return False

    async def push_status(self):
        await self._send_or_queue(self.status_payload())

    async def push_scan(self, rfid, action):
        await self._send_or_queue(
            {
                "type": "scan",
                "rfid": rfid,
                "action": action,
                "device_role": self.device_role,
                "device_id": self.device_id,
            }
        )

    async def send_ack(self, command_id, cmd, status, reason="ok", mode=None):
        if mode is None:
            mode = self.get_state()
        payload = {
            "type": "ACK",
            "command_id": command_id or "",
            "cmd": cmd or "",
            "status": status,
            "reason": reason,
            "mode": mode,
            "device_id": self.device_id,
            "ts": time.time() if hasattr(time, "time") else 0,
        }
        await self._send_or_queue(payload)

    async def _await_mode_applied(self):
        """Wait until HardwareManager dry-switch task finishes (applied)."""
        task = getattr(self.hw, "current_task", None)
        if not task:
            await asyncio.sleep(0.05)
            return
        try:
            await task
        except asyncio.CancelledError:
            pass
        except Exception as e:
            print("[CLOUD] mode task error:", e)

    async def apply_mode(self, mode, source="remote", command_id=None, cmd="SET_MODE"):
        if self.get_learn():
            print("[CLOUD] Reject mode while LEARN_MODE")
            if command_id is not None:
                await self.send_ack(command_id, cmd, "rejected", "learn_mode")
            return False
        try:
            mode = int(mode)
        except Exception:
            if command_id is not None:
                await self.send_ack(command_id, cmd, "rejected", "bad_mode")
            return False
        if mode not in (0, 1, 2):
            if command_id is not None:
                await self.send_ack(command_id, cmd, "rejected", "bad_mode")
            return False

        if command_id is not None:
            await self.send_ack(command_id, cmd, "accepted", "ok", mode)

        self.set_state(mode)
        self.hw.change_mode(mode)
        if mode == 1:
            asyncio.create_task(self.hw.beep_cooler_slow())
        elif mode == 2:
            asyncio.create_task(self.hw.beep_cooler_fast())
        else:
            asyncio.create_task(self.hw.beep_cooler_off())

        # applied only after dry-switch / kick-start sequence completes
        await self._await_mode_applied()
        await self.push_status()
        if command_id is not None:
            await self.send_ack(command_id, cmd, "applied", "ok", mode)
        print("[CLOUD] SET_MODE", mode, "from", source)
        return True

    async def cycle(self, source="remote", command_id=None):
        if self.get_learn():
            if command_id is not None:
                await self.send_ack(command_id, "CYCLE", "rejected", "learn_mode")
            return False
        nxt = (self.get_state() + 1) % 3
        return await self.apply_mode(nxt, source=source, command_id=command_id, cmd="CYCLE")

    async def drain_outbox(self):
        """Send queued uplink without dropping unsent records on failure."""
        if not self.outbox or not self.ws or not self.ws.open:
            return
        records = self.outbox.peek()
        if not records:
            return
        sent = 0
        for i, rec in enumerate(records):
            try:
                await self.ws.send_json(rec)
                sent = i + 1
            except Exception as e:
                print("[CLOUD] outbox resend failed:", e)
                break
        remaining = records[sent:]
        self.outbox.replace_all(remaining)
        if sent:
            print("[CLOUD] outbox drained", sent, "remaining", len(remaining))

    async def handle_command(self, raw):
        try:
            if isinstance(raw, str):
                msg = json.loads(raw)
            else:
                msg = raw
        except Exception:
            return

        if msg.get("type") == "ACK":
            return

        cmd = msg.get("cmd")
        if not cmd:
            return
        command_id = msg.get("command_id")

        if cmd == "OPEN":
            print("[CLOUD] Ignoring OPEN (door command)")
            if command_id:
                await self.send_ack(command_id, cmd, "rejected", "denied")
            return
        if cmd == "DENY":
            asyncio.create_task(self.hw.beep_denied())
            return
        if cmd == "GET_STATUS":
            await self.push_status()
            return

        # Downlink SET_MODE/CYCLE must carry command_id (ACK contract)
        if cmd in ("SET_MODE", "CYCLE"):
            if not command_id:
                print("[CLOUD] Reject", cmd, "missing command_id")
                await self.send_ack("", cmd, "rejected", "denied")
                return
            if cmd == "SET_MODE":
                await self.apply_mode(
                    msg.get("mode"), source="ws", command_id=command_id, cmd="SET_MODE"
                )
            else:
                await self.cycle(source="ws", command_id=command_id)
            return
