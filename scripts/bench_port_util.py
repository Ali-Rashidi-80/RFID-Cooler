#!/usr/bin/env python3
"""COM port helpers for bench_live.ps1 / flash_device.ps1 (Windows)."""

from __future__ import annotations

import sys

try:
    from serial.tools import list_ports
except ImportError:
    import subprocess

    subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", "pyserial"])
    from serial.tools import list_ports

_USB_KEYWORDS = (
    "usb",
    "serial",
    "ch340",
    "cp210",
    "ftdi",
    "silicon",
    "enhanced",
    "uart",
    "jtag",
)


def _score(port) -> int:
    desc = (port.description or "").lower()
    hwid = (port.hwid or "").lower()
    return sum(1 for k in _USB_KEYWORDS if k in desc or k in hwid)


def cmd_list() -> None:
    for p in list_ports.comports():
        print(f"{p.device}\t{p.description}\t{p.hwid}")


def cmd_best(preferred: str = "") -> None:
    if preferred:
        print(preferred.strip())
        return
    candidates = []
    for p in list_ports.comports():
        desc = (p.description or "").lower()
        if p.device.upper() == "COM1" and "communications" in desc:
            continue
        candidates.append((_score(p), p.device))
    candidates.sort(reverse=True)
    print(candidates[0][1] if candidates else "")


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: bench_port_util.py list|best [COMx]", file=sys.stderr)
        return 1
    op = sys.argv[1]
    if op == "list":
        cmd_list()
    elif op == "best":
        cmd_best(sys.argv[2] if len(sys.argv) > 2 else "")
    else:
        print("unknown op", op, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
