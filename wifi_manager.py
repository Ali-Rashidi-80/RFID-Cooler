# Non-blocking STA WiFi helper for MicroPython / ESP32
import network
import uasyncio as asyncio


class WifiManager:
    def __init__(self, ssid, password, check_interval_s=5):
        self.ssid = ssid or ""
        self.password = password or ""
        self.check_interval_s = check_interval_s
        self.wlan = network.WLAN(network.STA_IF)
        self._backoff_s = 2

    def is_connected(self):
        try:
            return self.wlan.active() and self.wlan.isconnected()
        except Exception:
            return False

    def connect_once(self):
        if not self.ssid:
            return False
        try:
            if not self.wlan.active():
                self.wlan.active(True)
            if self.wlan.isconnected():
                return True
            print("[WIFI] Connecting...")
            self.wlan.connect(self.ssid, self.password)
            return False
        except Exception as e:
            print("[WIFI] Connect error:", e)
            return False

    async def ensure_loop(self):
        """Background task: keep trying without blocking RFID."""
        while True:
            try:
                if not self.ssid:
                    await asyncio.sleep(30)
                    continue
                if self.is_connected():
                    self._backoff_s = 2
                    await asyncio.sleep(self.check_interval_s)
                    continue
                self.connect_once()
                # give radio time; RFID loop stays responsive
                waited = 0
                while waited < 8 and not self.is_connected():
                    await asyncio.sleep(0.5)
                    waited += 0.5
                if self.is_connected():
                    print("[WIFI] Connected:", self.wlan.ifconfig())
                    self._backoff_s = 2
                else:
                    print("[WIFI] Not connected; retry in", self._backoff_s, "s")
                    await asyncio.sleep(self._backoff_s)
                    self._backoff_s = min(self._backoff_s * 2, 60)
            except Exception as e:
                print("[WIFI] Loop error:", e)
                await asyncio.sleep(5)
