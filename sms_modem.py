# SIM800L UART SMS command channel: COOLER <pin> OFF|SLOW|FAST|CYCLE
import uasyncio as asyncio
from machine import UART
import time


class SmsModem:
    def __init__(self, tx, rx, pin, apply_mode, cycle, baud=9600):
        self.pin = str(pin)
        self.apply_mode = apply_mode
        self.cycle = cycle
        self.uart = UART(2, baudrate=baud, tx=tx, rx=rx)
        self._buf = b""

    async def _at(self, cmd, wait_s=1.0):
        try:
            self.uart.write(cmd + b"\r\n")
        except Exception:
            return b""
        await asyncio.sleep(wait_s)
        try:
            return self.uart.read() or b""
        except Exception:
            return b""

    async def setup(self):
        await self._at(b"AT")
        await self._at(b"ATE0")
        await self._at(b"AT+CMGF=1")
        await self._at(b'AT+CNMI=2,2,0,0,0')
        print("[SMS] Modem ready")

    def _handle_text(self, text):
        # COOLER <pin> OFF|SLOW|FAST|CYCLE
        parts = text.strip().split()
        if len(parts) < 3 or parts[0].upper() != "COOLER":
            return None
        if parts[1] != self.pin:
            print("[SMS] bad pin")
            return None
        return parts[2].upper()

    async def poll_loop(self):
        await self.setup()
        while True:
            try:
                chunk = self.uart.read()
                if chunk:
                    self._buf += chunk
                    if b"\n" in self._buf or b"\r" in self._buf:
                        try:
                            text = self._buf.decode("utf-8", "ignore")
                        except Exception:
                            text = str(self._buf)
                        self._buf = b""
                        # Extract SMS body after +CMT header
                        body = text
                        if "\n" in text:
                            lines = [ln.strip() for ln in text.replace("\r", "\n").split("\n") if ln.strip()]
                            body = lines[-1] if lines else text
                        action = self._handle_text(body)
                        if action == "OFF":
                            await self.apply_mode(0, source="sms")
                        elif action == "SLOW":
                            await self.apply_mode(1, source="sms")
                        elif action == "FAST":
                            await self.apply_mode(2, source="sms")
                        elif action == "CYCLE":
                            await self.cycle(source="sms")
            except Exception as e:
                print("[SMS] Error:", e)
            await asyncio.sleep(0.3)
