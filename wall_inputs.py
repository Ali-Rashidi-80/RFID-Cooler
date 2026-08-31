# Optional dry-contact wall switch inputs -> change_mode
# ESP32 note: GPIO 34/35/36/39 are input-only and have NO internal pull-up.
# Defaults use GPIOs that support internal pull-up; override via config.
import uasyncio as asyncio
from machine import Pin
import time

# Safe defaults with internal pull-up (avoid 34/35 unless external pull-ups fitted).
# Do not overlap SMS UART defaults (tx=26/rx=25) or RF433 (27).
DEFAULT_PINS = {
    0: 33,  # Off
    1: 14,  # Slow
    2: 15,  # Fast
}

# GPIOs that cannot enable internal PULL_UP on classic ESP32
_NO_INTERNAL_PULL = (34, 35, 36, 39)


class WallInputs:
    def __init__(self, apply_mode, pin_map=None, active_low=True):
        self.apply_mode = apply_mode
        self.active_low = active_low
        self.pin_map = pin_map or DEFAULT_PINS
        self.pins = {}
        self._last_mode = None
        self._last_change = 0
        for mode, gpio in self.pin_map.items():
            gpio = int(gpio)
            try:
                if gpio in _NO_INTERNAL_PULL:
                    # Require external pull-up to 3V3
                    self.pins[int(mode)] = Pin(gpio, Pin.IN)
                    print("[WALL] GPIO", gpio, "input-only (external pull-up required)")
                else:
                    self.pins[int(mode)] = Pin(gpio, Pin.IN, Pin.PULL_UP)
            except Exception as e:
                print("[WALL] Pin init failed", gpio, e)

    def _pressed(self, pin):
        try:
            v = pin.value()
            return (v == 0) if self.active_low else (v == 1)
        except Exception:
            return False

    async def poll_loop(self, debounce_ms=200):
        while True:
            try:
                active = None
                for mode, pin in self.pins.items():
                    if self._pressed(pin):
                        active = mode
                        break
                now = time.ticks_ms()
                if active is not None and active != self._last_mode:
                    if time.ticks_diff(now, self._last_change) > debounce_ms:
                        self._last_mode = active
                        self._last_change = now
                        print("[WALL] Mode", active)
                        await self.apply_mode(active, source="wall")
                elif active is None:
                    self._last_mode = None
            except Exception as e:
                print("[WALL] Error:", e)
            await asyncio.sleep(0.05)
