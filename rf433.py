# Cheap 433MHz ASK receiver learn/map -> cooler modes (Iran market remotes)
import uasyncio as asyncio
from machine import Pin
import json
import os
import time

CODES_FILE = "rf_codes.json"
TMP_FILE = "rf_codes.tmp"


class Rf433Learner:
    """
    Best-effort pulse decoder for common fixed-code remotes.
    Learn mode: hold learn_gpio or call enter_learn(slot) then press remote.
    Slots: off / slow / fast / cycle
    """

    def __init__(self, pin, apply_mode, cycle, learn_hold_ms=5000):
        self.pin = Pin(int(pin), Pin.IN)
        self.apply_mode = apply_mode
        self.cycle = cycle
        self.learn_hold_ms = learn_hold_ms
        self.codes = self._load()
        self.learn_slot = None
        self._last_code = None
        self._last_fire = 0

    def _load(self):
        try:
            with open(CODES_FILE, "r") as f:
                return json.load(f)
        except Exception:
            return {"off": None, "slow": None, "fast": None, "cycle": None}

    def _save(self):
        try:
            with open(TMP_FILE, "w") as f:
                json.dump(self.codes, f)
            try:
                os.remove(CODES_FILE)
            except OSError:
                pass
            os.rename(TMP_FILE, CODES_FILE)
        except Exception as e:
            print("[RF433] save error:", e)

    def enter_learn(self, slot):
        if slot in self.codes:
            self.learn_slot = slot
            print("[RF433] Learning slot:", slot)

    def _sample_code(self, timeout_ms=120):
        """Very light pulse-length hash; good enough for learn/match on stable remotes."""
        t0 = time.ticks_ms()
        last = self.pin.value()
        edges = []
        last_t = time.ticks_us()
        while time.ticks_diff(time.ticks_ms(), t0) < timeout_ms:
            v = self.pin.value()
            if v != last:
                now = time.ticks_us()
                edges.append(time.ticks_diff(now, last_t))
                last_t = now
                last = v
                if len(edges) > 80:
                    break
        if len(edges) < 12:
            return None
        # Quantize and hash
        h = 0
        for d in edges[:48]:
            q = int(d / 100)
            h = (h * 33 + q) & 0xFFFFFFFF
        return h

    async def poll_loop(self):
        print("[RF433] Listening on GPIO")
        while True:
            try:
                # Wait for activity
                if self.pin.value() == 0:
                    await asyncio.sleep(0.01)
                    continue
                code = self._sample_code()
                if code is None:
                    await asyncio.sleep(0.02)
                    continue
                now = time.ticks_ms()
                if code == self._last_code and time.ticks_diff(now, self._last_fire) < 800:
                    await asyncio.sleep(0.05)
                    continue
                self._last_code = code
                self._last_fire = now

                if self.learn_slot:
                    self.codes[self.learn_slot] = code
                    self._save()
                    print("[RF433] Learned", self.learn_slot, code)
                    self.learn_slot = None
                    await asyncio.sleep(0.5)
                    continue

                for slot, val in self.codes.items():
                    if val is not None and int(val) == int(code):
                        print("[RF433] Match", slot)
                        if slot == "off":
                            await self.apply_mode(0, source="rf433")
                        elif slot == "slow":
                            await self.apply_mode(1, source="rf433")
                        elif slot == "fast":
                            await self.apply_mode(2, source="rf433")
                        elif slot == "cycle":
                            await self.cycle(source="rf433")
                        break
            except Exception as e:
                print("[RF433] Error:", e)
            await asyncio.sleep(0.02)
