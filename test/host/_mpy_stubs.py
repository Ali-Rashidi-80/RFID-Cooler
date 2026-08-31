"""Install MicroPython module stubs before importing firmware modules on CPython."""

from __future__ import annotations

import asyncio
import sys
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def install() -> None:
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))

    uasyncio = types.ModuleType("uasyncio")
    for name in (
        "sleep",
        "wait_for",
        "create_task",
        "run",
        "TimeoutError",
        "open_connection",
        "start_server",
    ):
        if hasattr(asyncio, name):
            setattr(uasyncio, name, getattr(asyncio, name))

    async def _noop_to_thread(fn, *args, **kwargs):
        return fn(*args, **kwargs)

    if not hasattr(uasyncio, "to_thread"):
        uasyncio.to_thread = _noop_to_thread

    sys.modules["uasyncio"] = uasyncio

    network = types.ModuleType("network")

    class _IF:
        STA_IF = 0
        AP_IF = 1

    class _WLAN:
        def __init__(self, _if):
            self._if = _if
            self._active = False
            self._connected = False

        def active(self, state=None):
            if state is None:
                return self._active
            self._active = bool(state)
            return None

        def isconnected(self):
            return self._connected

        def connect(self, *_a, **_k):
            pass

        def config(self, **_k):
            pass

        def ifconfig(self):
            return ("192.168.4.1", "255.255.255.0", "192.168.4.1", "8.8.8.8")

    network.STA_IF = _IF.STA_IF
    network.AP_IF = _IF.AP_IF
    network.WLAN = _WLAN
    sys.modules["network"] = network

    machine = types.ModuleType("machine")

    class Pin:
        IN = 0
        OUT = 1
        PULL_UP = 2

        def __init__(self, *_a, **_k):
            self._v = 1

        def value(self, v=None):
            if v is None:
                return self._v
            self._v = v

    class UART:
        def __init__(self, *_a, **_k):
            pass

        def write(self, _b):
            pass

        def read(self):
            return None

    machine.Pin = Pin
    machine.UART = UART
    sys.modules["machine"] = machine
