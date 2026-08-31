# SoftAP helper for local setup / offline control
import network


def _normalize_ap_password(password):
    """WPA2 needs >=8 chars; repeat local_pin so PSK derives from the same PIN."""
    pw = str(password or "1234")
    if not pw:
        pw = "1234"
    while len(pw) < 8:
        pw = pw + pw
    return pw[:63]


class ApManager:
    def __init__(self, ssid, password, channel=1):
        self.ssid = (ssid or "Cooler-AP")[:32]
        self.password = _normalize_ap_password(password)
        self.channel = channel
        self.ap = network.WLAN(network.AP_IF)
        self._active = False

    def start(self, disable_sta=False):
        try:
            if disable_sta:
                try:
                    sta = network.WLAN(network.STA_IF)
                    if sta.active():
                        sta.active(False)
                        print("[AP] STA disabled for setup")
                except Exception as e:
                    print("[AP] STA disable warn:", e)
            self.ap.active(True)
            # AUTH_WPA_WPA2_PSK = 3 on ESP32 MicroPython
            self.ap.config(
                essid=self.ssid,
                password=self.password,
                authmode=3,
                channel=self.channel,
            )
            self._active = True
            print("[AP] Started", self.ssid, self.ap.ifconfig())
            return True
        except Exception as e:
            print("[AP] Start failed:", e)
            self._active = False
            return False

    def stop(self):
        try:
            if self.ap.active():
                self.ap.active(False)
            self._active = False
            print("[AP] Stopped")
        except Exception as e:
            print("[AP] Stop error:", e)

    def is_active(self):
        try:
            return self.ap.active() and self._active
        except Exception:
            return False

    def ip(self):
        try:
            return self.ap.ifconfig()[0]
        except Exception:
            return "192.168.4.1"
