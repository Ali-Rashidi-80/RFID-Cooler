#!/usr/bin/env python3
"""Host-side honest tests — MicroPython modules stubbed; no fake green without assertions."""

from __future__ import annotations

import asyncio
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HOST_TEST = ROOT / "test" / "host"
sys.path.insert(0, str(HOST_TEST))

from _mpy_stubs import install  # noqa: E402

install()

from ap_manager import _normalize_ap_password  # noqa: E402
from cloud import CloudBridge  # noqa: E402
from outbox import Outbox  # noqa: E402
import ota_stub  # noqa: E402


def build_ws_path(ws_path: str, token: str, role: str, device_id: str) -> str:
    """Contract mirror of main.cloud_session_loop path builder."""
    sep = "&" if "?" in ws_path else "?"
    return "{}{}token={}&role={}&device_id={}".format(
        ws_path, sep, token, role, device_id
    )


class MockHW:
    def __init__(self):
        self.current_task = None
        self.modes = []

    def change_mode(self, mode):
        self.modes.append(int(mode))
        self.current_task = None

    async def beep_cooler_slow(self):
        pass

    async def beep_cooler_fast(self):
        pass

    async def beep_cooler_off(self):
        pass

    async def beep_denied(self):
        pass


class TestApPassword(unittest.TestCase):
    def test_repeat_short_pin_to_eight_chars(self):
        self.assertEqual(_normalize_ap_password("1234"), "12341234")

    def test_long_pin_truncated_at_63(self):
        self.assertEqual(len(_normalize_ap_password("x" * 100)), 63)

    def test_empty_falls_back(self):
        self.assertEqual(_normalize_ap_password(""), "12341234")


class TestWsPathContract(unittest.TestCase):
    def test_no_existing_query(self):
        p = build_ws_path("/ws/hardware", "tok", "cooler", "c-1")
        self.assertEqual(p, "/ws/hardware?token=tok&role=cooler&device_id=c-1")

    def test_existing_query_uses_ampersand(self):
        p = build_ws_path("/ws/hardware?x=1", "tok", "cooler", "c-1")
        self.assertTrue(p.startswith("/ws/hardware?x=1&token="))
        self.assertIn("role=cooler", p)
        self.assertIn("device_id=c-1", p)


class TestOutbox(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.path = os.path.join(self.tmp, "outbox.jsonl")

    def test_append_peek_replace_atomic_clear(self):
        ob = Outbox(enabled=True, path=self.path)
        ob.append({"type": "status", "n": 1})
        ob.append({"type": "scan", "n": 2})
        records = ob.peek()
        self.assertEqual(len(records), 2)
        self.assertEqual(records[0]["type"], "status")

        ob.replace_all([records[1]])
        self.assertEqual(len(ob.peek()), 1)
        self.assertEqual(ob.peek()[0]["type"], "scan")

        ob.replace_all([])
        self.assertEqual(ob.peek(), [])
        self.assertFalse(os.path.exists(self.path))

    def test_disabled_no_write(self):
        ob = Outbox(enabled=False, path=self.path)
        ob.append({"type": "x"})
        self.assertFalse(os.path.exists(self.path))


class TestOtaStub(unittest.TestCase):
    def test_not_implemented_is_honest(self):
        r = ota_stub.ota_not_implemented()
        self.assertFalse(r["ok"])
        self.assertEqual(r["reason"], "ota_deferred")


class TestCloudBridge(unittest.TestCase):
    def _bridge(self, learn=False, state=0):
        hw = MockHW()
        st = {"v": state, "learn": learn}

        async def get_state():
            return st["v"]

        def set_state(v):
            st["v"] = int(v)

        def get_learn():
            return st["learn"]

        return (
            CloudBridge(hw, lambda: st["v"], set_state, get_learn, outbox=None),
            hw,
            st,
        )

    def test_status_payload_shape(self):
        b, _, _ = self._bridge(state=2)
        b.device_id = "cooler-001"
        b.device_role = "cooler"
        p = b.status_payload()
        self.assertEqual(p["type"], "status")
        self.assertEqual(p["cooler_state"], 2)
        self.assertEqual(p["device_role"], "cooler")
        self.assertIn("learn_mode", p)

    def test_open_door_command_rejected_with_ack(self):
        async def run():
            b, hw, _ = self._bridge()
            b.device_id = "c1"
            sent = []

            class WS:
                open = True

                async def send_json(self, obj):
                    sent.append(obj)
                    return True

            b.attach_ws(WS(), "c1", "cooler")
            await b.handle_command(
                json.dumps({"cmd": "OPEN", "command_id": "door-1"})
            )
            self.assertEqual(hw.modes, [])
            acks = [x for x in sent if x.get("type") == "ACK"]
            self.assertEqual(len(acks), 1)
            self.assertEqual(acks[0]["status"], "rejected")
            self.assertEqual(acks[0]["reason"], "denied")

        asyncio.run(run())

    def test_set_mode_without_command_id_rejected(self):
        async def run():
            b, hw, _ = self._bridge()
            sent = []

            class WS:
                open = True

                async def send_json(self, obj):
                    sent.append(obj)
                    return True

            b.attach_ws(WS(), "c1", "cooler")
            await b.handle_command(json.dumps({"cmd": "SET_MODE", "mode": 2}))
            self.assertEqual(hw.modes, [])
            acks = [x for x in sent if x.get("type") == "ACK"]
            self.assertTrue(acks)
            self.assertEqual(acks[0]["status"], "rejected")

        asyncio.run(run())

    def test_set_mode_learn_mode_rejected(self):
        async def run():
            b, hw, st = self._bridge(learn=True)
            st["learn"] = True
            sent = []

            class WS:
                open = True

                async def send_json(self, obj):
                    sent.append(obj)
                    return True

            b.attach_ws(WS(), "c1", "cooler")
            await b.handle_command(
                json.dumps(
                    {"cmd": "SET_MODE", "mode": 1, "command_id": "abc"}
                )
            )
            self.assertEqual(hw.modes, [])
            acks = [x for x in sent if x.get("type") == "ACK"]
            self.assertEqual(acks[-1]["status"], "rejected")
            self.assertEqual(acks[-1]["reason"], "learn_mode")

        asyncio.run(run())

    def test_set_mode_applied_ack_sequence(self):
        async def run():
            b, hw, st = self._bridge(state=0)
            sent = []

            class WS:
                open = True

                async def send_json(self, obj):
                    sent.append(obj)
                    return True

            b.attach_ws(WS(), "c1", "cooler")
            ok = await b.apply_mode(2, source="test", command_id="x1", cmd="SET_MODE")
            self.assertTrue(ok)
            self.assertEqual(st["v"], 2)
            self.assertEqual(hw.modes, [2])
            acks = [x for x in sent if x.get("type") == "ACK"]
            statuses = [a["status"] for a in acks]
            self.assertEqual(statuses, ["accepted", "applied"])

        asyncio.run(run())

    def test_cycle_wraps_off_to_slow(self):
        async def run():
            b, hw, st = self._bridge(state=0)
            b.ws = None
            ok = await b.cycle(source="test", command_id="c1")
            self.assertTrue(ok)
            self.assertEqual(st["v"], 1)
            self.assertEqual(hw.modes, [1])

        asyncio.run(run())

    def test_outbox_queue_when_ws_down(self):
        async def run():
            b, _, _ = self._bridge()
            with tempfile.TemporaryDirectory() as td:
                path = os.path.join(td, "ob.jsonl")
                b.outbox = Outbox(enabled=True, path=path)
                b.ws = None
                await b.push_status()
                rows = b.outbox.peek()
                self.assertEqual(len(rows), 1)
                self.assertEqual(rows[0]["type"], "status")

        asyncio.run(run())


class TestLocalHttpHelpers(unittest.TestCase):
    def setUp(self):
        from local_http import LocalHttpServer

        self.http = LocalHttpServer(
            apply_mode=None,
            cycle=None,
            get_state=lambda: 0,
            get_learn=lambda: False,
            local_pin="4242",
        )

    def test_parse_query_string(self):
        base, qs = self.http._parse_qs("/api/command?pin=4242&x=1")
        self.assertEqual(base, "/api/command")
        self.assertEqual(qs["pin"], "4242")
        self.assertEqual(qs["x"], "1")

    def test_pin_header_or_query(self):
        ok_h = self.http._check_pin({"x-local-pin": "4242"}, {})
        ok_q = self.http._check_pin({}, {"pin": "4242"})
        bad = self.http._check_pin({"x-local-pin": "0000"}, {})
        self.assertTrue(ok_h)
        self.assertTrue(ok_q)
        self.assertFalse(bad)

    def test_http_reason_phrases_not_always_ok(self):
        src = (ROOT / "local_http.py").read_text(encoding="utf-8")
        self.assertIn("_HTTP_REASON", src)
        self.assertIn("401", src)
        self.assertNotIn('%d OK\\r\\nContent-Type: %s', src)


class TestCloudGetStatus(unittest.TestCase):
    def test_get_status_uplink(self):
        async def run():
            hw = MockHW()
            st = {"v": 1, "learn": False}
            b = CloudBridge(hw, lambda: st["v"], lambda v: st.update(v=int(v)), lambda: st["learn"])
            sent = []

            class WS:
                open = True

                async def send_json(self, obj):
                    sent.append(obj)
                    return True

            b.attach_ws(WS(), "dev-1", "cooler")
            await b.handle_command(json.dumps({"cmd": "GET_STATUS"}))
            status = [x for x in sent if x.get("type") == "status"]
            self.assertEqual(len(status), 1)
            self.assertEqual(status[0]["cooler_state"], 1)

        asyncio.run(run())


class TestRf433AtomicSave(unittest.TestCase):
    def test_save_uses_tmp_then_rename(self):
        from rf433 import Rf433Learner

        with tempfile.TemporaryDirectory() as td:
            orig_codes = Path(td) / "rf_codes.json"
            orig_tmp = Path(td) / "rf_codes.tmp"
            # Patch module-level names by instance paths — use real files in tmp
            learner = Rf433Learner(27, apply_mode=None, cycle=None)
            learner.codes = {"off": 1, "slow": None, "fast": None, "cycle": None}
            # Override file paths for test isolation
            import rf433 as rf433_mod

            rf433_mod.CODES_FILE = str(orig_codes)
            rf433_mod.TMP_FILE = str(orig_tmp)
            learner._save()
            self.assertTrue(orig_codes.is_file())
            self.assertFalse(orig_tmp.exists())
            data = json.loads(orig_codes.read_text(encoding="utf-8"))
            self.assertEqual(data["off"], 1)


class TestSmsCommandParser(unittest.TestCase):
    def test_valid_commands(self):
        from sms_modem import SmsModem

        m = SmsModem(26, 25, "9999", apply_mode=None, cycle=None)
        self.assertEqual(m._handle_text("COOLER 9999 OFF"), "OFF")
        self.assertEqual(m._handle_text("cooler 9999 slow"), "SLOW")
        self.assertIsNone(m._handle_text("COOLER 0000 OFF"))
        self.assertIsNone(m._handle_text("DOOR 9999 OPEN"))


class TestConfigAndDocsContract(unittest.TestCase):
    def test_config_example_has_all_documented_keys(self):
        example = json.loads((ROOT / "config.example.json").read_text(encoding="utf-8"))
        required = {
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
        }
        missing = required - set(example.keys())
        self.assertFalse(missing, f"missing config keys: {missing}")
        self.assertEqual(example["device_role"], "cooler")

    def test_main_pin_constants_match_readme(self):
        main_src = (ROOT / "main.py").read_text(encoding="utf-8")
        contracts = {
            "PIN_BUZZER = 17": "Buzzer | 17",
            "PIN_RELAY_MAIN_SSR = 16": "SSR | 16",
            "PIN_RELAY_SPEED_MECH = 32": "Mechanical | 32",
            "CS_PIN = 5": "GPIO 5",
            "SCK_PIN = 18": "GPIO 18",
            "MOSI_PIN = 23": "GPIO 23",
            "MISO_PIN = 19": "GPIO 19",
            "RST_PIN = 4": "GPIO 4",
        }
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        for main_line, readme_fragment in contracts.items():
            self.assertIn(main_line, main_src, main_line)
            self.assertIn(readme_fragment, readme, readme_fragment)

    def test_required_repo_files_exist(self):
        paths = [
            "README.md",
            "README.fa.md",
            "LICENSE",
            ".github/workflows/ci.yml",
            "assets/logo.svg",
            "assets/logo-3d.png",
            "docs/README.md",
            "docs/OTA.md",
            "docs/PRODUCT_ROADMAP_RESILIENCE.md",
            "docs/IRAN_MIRRORS.md",
            "scripts/validate.py",
        ]
        for rel in paths:
            self.assertTrue((ROOT / rel).is_file(), rel)


if __name__ == "__main__":
    unittest.main(verbosity=2)
