#!/usr/bin/env python3
"""Static validation for RFID-Cooler firmware sources (host-side, no ESP32)."""

from __future__ import annotations

import ast
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

PY_DIRS = ("", "test")
PY_SKIP = frozenset({"test/host"})
CONFIG_EXAMPLE = ROOT / "config.example.json"

ALL_CONFIG_KEYS = (
    "wifi_ssid",
    "wifi_pass",
    "server_host",
    "server_port",
    "use_ssl",
    "ws_path",
    "hardware_token",
    "device_id",
    "device_role",
    "online_enabled",
    "temp_enabled",
    "ap_enabled",
    "lan_http_enabled",
    "local_pin",
    "outbox_enabled",
    "wall_enabled",
    "wall_pin_off",
    "wall_pin_slow",
    "wall_pin_fast",
    "rf433_enabled",
    "rf433_pin",
    "ble_enabled",
    "ble_pin",
    "sms_uart_enabled",
    "sms_uart_tx",
    "sms_uart_rx",
    "sms_pin",
    "mqtt_enabled",
    "mqtt_host",
    "mqtt_port",
    "mqtt_topic_prefix",
    "alert_phone",
)

REQUIRED_REPO_FILES = (
    "README.md",
    "README.fa.md",
    "LICENSE",
    "INSTALL.md",
    "CONTRIBUTING.md",
    "SECURITY.md",
    ".github/workflows/ci.yml",
    "assets/logo.svg",
    "assets/logo-3d.png",
    "docs/README.md",
    "docs/OTA.md",
    "docs/PRODUCT_ROADMAP_RESILIENCE.md",
    "docs/IRAN_MIRRORS.md",
    "docs/SKU_LITE_SMART_PLUG.md",
    "docs/HARDWARE_BENCH.md",
    "scripts/flash_device.ps1",
    "scripts/bench_live.ps1",
    "config.bench.example.json",
)

PIN_CONTRACT = {
    "PIN_BUZZER = 17": "Buzzer | 17",
    "PIN_RELAY_MAIN_SSR = 16": "SSR | 16",
    "PIN_RELAY_SPEED_MECH = 32": "Mechanical | 32",
    "CS_PIN = 5": "GPIO 5",
    "SCK_PIN = 18": "GPIO 18",
    "MOSI_PIN = 23": "GPIO 23",
    "MISO_PIN = 19": "GPIO 19",
    "RST_PIN = 4": "GPIO 4",
}


def iter_py_files() -> list[Path]:
    files: list[Path] = []
    for sub in PY_DIRS:
        base = ROOT / sub if sub else ROOT
        if not base.is_dir():
            continue
        for path in sorted(base.glob("*.py")):
            rel = path.relative_to(ROOT).as_posix()
            if rel.startswith("test/host"):
                continue
            files.append(path)
    return files


def check_syntax(path: Path) -> list[str]:
    source = path.read_text(encoding="utf-8")
    errors: list[str] = []
    try:
        ast.parse(source, filename=str(path))
    except SyntaxError as exc:
        errors.append(f"{path}: syntax error line {exc.lineno}: {exc.msg}")
    return errors


def check_config_example() -> list[str]:
    errors: list[str] = []
    if not CONFIG_EXAMPLE.is_file():
        return [f"missing {CONFIG_EXAMPLE.name}"]
    try:
        data = json.loads(CONFIG_EXAMPLE.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return [f"{CONFIG_EXAMPLE.name}: invalid JSON — {exc}"]
    for key in ALL_CONFIG_KEYS:
        if key not in data:
            errors.append(f"{CONFIG_EXAMPLE.name}: missing key '{key}'")
    if data.get("device_role") != "cooler":
        errors.append(f"{CONFIG_EXAMPLE.name}: device_role must be 'cooler'")
    return errors


def check_repo_files() -> list[str]:
    errors: list[str] = []
    for rel in REQUIRED_REPO_FILES:
        if not (ROOT / rel).is_file():
            errors.append(f"missing required file: {rel}")
    return errors


def check_pin_readme_contract() -> list[str]:
    errors: list[str] = []
    main_path = ROOT / "main.py"
    readme_path = ROOT / "README.md"
    if not main_path.is_file() or not readme_path.is_file():
        return errors
    main_src = main_path.read_text(encoding="utf-8")
    readme = readme_path.read_text(encoding="utf-8")
    for main_line, fragment in PIN_CONTRACT.items():
        if main_line not in main_src:
            errors.append(f"main.py missing pin contract: {main_line}")
        if fragment not in readme:
            errors.append(f"README.md missing pin doc: {fragment}")
    return errors


def check_readme_internal_links() -> list[str]:
    errors: list[str] = []
    readme = ROOT / "README.md"
    if not readme.is_file():
        return ["missing README.md"]
    text = readme.read_text(encoding="utf-8")
    for match in re.finditer(r"\]\(([^)#]+)\)", text):
        target = match.group(1).strip()
        if target.startswith("http") or target.startswith("../"):
            continue
        path = ROOT / target
        if not path.is_file():
            errors.append(f"README broken link: {target}")
    return errors


def check_local_http_status_reasons() -> list[str]:
    path = ROOT / "local_http.py"
    if not path.is_file():
        return ["missing local_http.py"]
    src = path.read_text(encoding="utf-8")
    if "_HTTP_REASON" not in src:
        return ["local_http.py must map HTTP status codes to reason phrases"]
    if '%d OK\r\nContent-Type' in src.replace(" ", ""):
        return ["local_http.py still emits 'N OK' for all status codes"]
    return []


def main() -> int:
    errors: list[str] = []
    py_files = iter_py_files()
    if not py_files:
        errors.append("no Python files found")
    for path in py_files:
        errors.extend(check_syntax(path))
    errors.extend(check_config_example())
    errors.extend(check_repo_files())
    errors.extend(check_pin_readme_contract())
    errors.extend(check_readme_internal_links())
    errors.extend(check_local_http_status_reasons())

    if errors:
        print("VALIDATE FAILED:")
        for err in errors:
            print(f"  - {err}")
        return 1

    print(
        f"VALIDATE OK — {len(py_files)} firmware .py files, "
        f"{len(ALL_CONFIG_KEYS)} config keys, docs/assets/CI"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
