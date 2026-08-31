# BLE GATT cooler control via aioble (optional; copy aioble onto device offline)
import uasyncio as asyncio
import json

# Custom 128-bit UUIDs
_SERVICE = "6e400001-b5a3-f393-e0a9-e50e24dcca9e"
_CHAR_CMD = "6e400002-b5a3-f393-e0a9-e50e24dcca9e"
_CHAR_STATUS = "6e400003-b5a3-f393-e0a9-e50e24dcca9e"


class BleControl:
    def __init__(self, apply_mode, cycle, get_state, pin="1234", name="Cooler"):
        self.apply_mode = apply_mode
        self.cycle = cycle
        self.get_state = get_state
        self.pin = str(pin)
        self.name = name[:20]

    async def run(self):
        try:
            import bluetooth
            import aioble
        except ImportError:
            print("[BLE] aioble/bluetooth not available — skip")
            return

        service = aioble.Service(bluetooth.UUID(_SERVICE))
        char_cmd = aioble.Characteristic(
            service, bluetooth.UUID(_CHAR_CMD), write=True, capture=True
        )
        char_status = aioble.Characteristic(
            service, bluetooth.UUID(_CHAR_STATUS), read=True, notify=True
        )
        aioble.register_services(service)
        print("[BLE] Advertising", self.name)

        async def status_loop(connection):
            while connection.is_connected():
                payload = json.dumps({"mode": self.get_state()}).encode()
                try:
                    char_status.write(payload)
                    char_status.notify(connection, payload)
                except Exception:
                    pass
                await asyncio.sleep(2)

        while True:
            try:
                async with await aioble.advertise(
                    250_000,
                    name=self.name,
                    services=[bluetooth.UUID(_SERVICE)],
                ) as connection:
                    print("[BLE] Connected", connection.device)
                    st = asyncio.create_task(status_loop(connection))
                    try:
                        while connection.is_connected():
                            _, data = await char_cmd.written()
                            try:
                                msg = json.loads(data.decode())
                            except Exception:
                                continue
                            if str(msg.get("pin", "")) != self.pin:
                                print("[BLE] bad pin")
                                continue
                            cmd = msg.get("cmd")
                            if cmd == "SET_MODE":
                                await self.apply_mode(msg.get("mode"), source="ble")
                            elif cmd == "CYCLE":
                                await self.cycle(source="ble")
                    finally:
                        st.cancel()
            except Exception as e:
                print("[BLE] Error:", e)
                await asyncio.sleep(2)
