# Optional lightweight MQTT client for local broker (R3)
# Uses umqtt.simple if present; otherwise no-op with log.
# check_msg / publish run via asyncio thread offload when available to avoid
# blocking the RFID/WDT loop under broker faults.
import uasyncio as asyncio
import json


class MqttCooler:
    def __init__(self, host, port, prefix, device_id, apply_mode, cycle, get_state):
        self.host = host
        self.port = int(port or 1883)
        self.prefix = prefix or "cooler"
        self.device_id = device_id
        self.apply_mode = apply_mode
        self.cycle = cycle
        self.get_state = get_state
        self.cmd_topic = "{}/{}/cmd".format(self.prefix, self.device_id)
        self.status_topic = "{}/{}/status".format(self.prefix, self.device_id)
        self._pending = None

    async def _call(self, fn, *args):
        """Best-effort non-blocking wrapper for sync umqtt calls."""
        try:
            return await asyncio.to_thread(fn, *args)
        except AttributeError:
            # MicroPython: no to_thread — yield then call briefly
            await asyncio.sleep(0)
            return fn(*args)

    async def run(self):
        try:
            from umqtt.simple import MQTTClient
        except ImportError:
            print("[MQTT] umqtt.simple missing — copy offline or disable mqtt_enabled")
            return

        client_id = b"cooler-" + self.device_id.encode()[:20]

        def _on_msg(topic, msg):
            try:
                self._pending = json.loads(msg)
            except Exception:
                return

        while True:
            c = None
            try:
                c = MQTTClient(client_id, self.host, port=self.port)
                c.set_callback(_on_msg)
                await self._call(c.connect)
                await self._call(c.subscribe, self.cmd_topic.encode())
                print("[MQTT] Connected", self.host, self.cmd_topic)
                while True:
                    await self._call(c.check_msg)
                    if self._pending:
                        data = self._pending
                        self._pending = None
                        cmd = data.get("cmd")
                        if cmd == "SET_MODE":
                            await self.apply_mode(data.get("mode"), source="mqtt")
                        elif cmd == "CYCLE":
                            await self.cycle(source="mqtt")
                    payload = json.dumps(
                        {"mode": self.get_state(), "device_id": self.device_id}
                    )
                    try:
                        await self._call(
                            c.publish,
                            self.status_topic.encode(),
                            payload.encode(),
                            True,
                        )
                    except TypeError:
                        # older umqtt: publish(topic, msg) without retain kw
                        await self._call(
                            c.publish, self.status_topic.encode(), payload.encode()
                        )
                    except Exception:
                        break
                    await asyncio.sleep(5)
            except Exception as e:
                print("[MQTT] Error:", e)
                try:
                    if c:
                        await self._call(c.disconnect)
                except Exception:
                    pass
                await asyncio.sleep(5)
