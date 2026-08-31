#!/usr/bin/env python3
"""Capture serial boot log for bench diagnostics."""

from __future__ import annotations

import sys
import time

try:
    import serial
except ImportError:
    import subprocess

    subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", "pyserial"])
    import serial


def main() -> int:
    if len(sys.argv) < 4:
        print("usage: bench_serial_snapshot.py COMx SECONDS LOGFILE", file=sys.stderr)
        return 1
    port, sec_s, log_path = sys.argv[1], int(sys.argv[2]), sys.argv[3]
    try:
        ser = serial.Serial(port, 115200, timeout=0.25)
    except Exception as exc:
        print(f"[bench] Cannot open {port}: {exc}")
        return 1
    try:
        ser.dtr = False
        time.sleep(0.1)
        ser.dtr = True
    except Exception:
        pass
    chunks: list[str] = []
    start = time.time()
    while time.time() - start < sec_s:
        try:
            data = ser.read(4096)
        except Exception:
            break
        if data:
            text = data.decode("utf-8", errors="replace")
            chunks.append(text)
            print(text, end="", flush=True)
    ser.close()
    body = "".join(chunks)
    with open(log_path, "w", encoding="utf-8") as f:
        f.write(body)
    print(f"\n[bench] Saved {len(body)} chars to {log_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
