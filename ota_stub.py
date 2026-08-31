# OTA placeholder (R3) — do not auto-flash in production without signed images.
# Documented workflow: mpremote/rshell copy of verified .mpy/.py after ACK drain.


def ota_not_implemented():
    return {
        "ok": False,
        "reason": "ota_deferred",
        "hint": "Use offline copy via mpremote after R1/R2 stability; enable signed OTA later.",
    }
