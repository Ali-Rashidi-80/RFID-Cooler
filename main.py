# Ali Rashidi
# t.me/WriteYourway
# Offline-first RFID cooler + optional online dual-mode

import uasyncio as asyncio
import machine
from machine import WDT, PWM, Pin, SPI
import json
import gc
import time
import os
from mfrc522 import MFRC522

# ==========================================
# 0. CONFIGURATION & STATE
# ==========================================
DEBUG_MODE = False

MASTER_CARD_UID = "0x38915e18"
MASTER_HOLD_TIME = 4000

CARDS_FILE = "cards.json"
TMP_FILE = "cards.tmp"
CONFIG_FILE = "config.json"

BUZZER_VOLUME = 120

COOLER_STATE = 0
LEARN_MODE = False
LEARN_MODE_TIMER = 0

# Online bridge (set in system_runner when enabled)
_cloud = None

# ==========================================
# 1. PINOUT CONFIGURATION
# ==========================================
SCK_PIN = 18
MISO_PIN = 19
MOSI_PIN = 23
CS_PIN = 5
RST_PIN = 4

PIN_BUZZER = 17
PIN_RELAY_MAIN_SSR = 16
PIN_RELAY_SPEED_MECH = 32


def load_config():
    try:
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return {}


# ==========================================
# 2. BULLETPROOF CARD MANAGEMENT
# ==========================================
def load_cards():
    try:
        with open(CARDS_FILE, "r") as f:
            return json.load(f)
    except Exception:
        try:
            with open(TMP_FILE, "r") as f:
                return json.load(f)
        except Exception:
            return []


def save_cards(cards):
    try:
        with open(TMP_FILE, "w") as f:
            json.dump(cards, f)
        try:
            os.remove(CARDS_FILE)
        except OSError:
            pass
        os.rename(TMP_FILE, CARDS_FILE)
    except Exception as e:
        print("[SYS] Error saving cards:", e)


def toggle_card(uid):
    cards = load_cards()
    if uid in cards:
        cards.remove(uid)
        save_cards(cards)
        return "REMOVED"
    cards.append(uid)
    save_cards(cards)
    return "ADDED"


# ==========================================
# 3. HARDWARE MANAGER
# ==========================================
class HardwareManager:
    def __init__(self):
        self.relay_main = machine.Pin(PIN_RELAY_MAIN_SSR, machine.Pin.OUT)
        self.relay_speed = machine.Pin(PIN_RELAY_SPEED_MECH, machine.Pin.OUT)
        self.current_task = None
        self.force_off()
        self.buzzer = PWM(Pin(PIN_BUZZER))
        self.buzzer.duty_u16(0)
        self.buzzer_lock = asyncio.Lock()
        self.init_rfid()

    def init_rfid(self):
        try:
            rst = Pin(RST_PIN, Pin.OUT)
            rst.off()
            time.sleep(0.05)
            rst.on()
            time.sleep(0.05)
            self.spi = SPI(
                1,
                baudrate=2500000,
                polarity=0,
                phase=0,
                sck=Pin(SCK_PIN),
                mosi=Pin(MOSI_PIN),
                miso=Pin(MISO_PIN),
            )
            self.rdr = MFRC522(spi=self.spi, cs=Pin(CS_PIN, Pin.OUT))
            print("[HW] RFID Initialized & Ready")
            return True
        except Exception as e:
            print("[HW] RFID Init Error:", e)
            self.rdr = None
            return False

    def force_off(self):
        # Active-Low: 1=OFF | 0=ON
        self.relay_main.value(1)
        self.relay_speed.value(1)

    def change_mode(self, mode):
        if self.current_task:
            self.current_task.cancel()
        if mode == 0:
            self.current_task = asyncio.create_task(self._task_off())
        elif mode == 1:
            self.current_task = asyncio.create_task(self._task_slow())
        elif mode == 2:
            self.current_task = asyncio.create_task(self._task_fast())

    async def _task_off(self):
        try:
            self.relay_main.value(1)
            await asyncio.sleep(0.1)
            self.relay_speed.value(1)
            print("[COOLER] OFF")
        except asyncio.CancelledError:
            self.force_off()

    async def _task_fast(self):
        try:
            self.relay_main.value(1)
            await asyncio.sleep(0.1)
            self.relay_speed.value(0)  # NO = fast (mech ON)
            await asyncio.sleep(0.05)
            self.relay_main.value(0)
            print("[COOLER] ON - FAST")
        except asyncio.CancelledError:
            self.force_off()

    async def _task_slow(self):
        try:
            print("[COOLER] ON - SLOW (KICK-STARTING IN FAST FOR 3s...)")
            self.relay_main.value(1)
            await asyncio.sleep(0.1)
            self.relay_speed.value(0)
            await asyncio.sleep(0.05)
            self.relay_main.value(0)
            await asyncio.sleep(3)
            print("[COOLER] KICK-START DONE. SWITCHING TO SLOW SAFELY...")
            self.relay_main.value(1)
            await asyncio.sleep(0.1)
            self.relay_speed.value(1)  # NC = slow (mech OFF)
            await asyncio.sleep(0.05)
            self.relay_main.value(0)
        except asyncio.CancelledError:
            print("[COOLER] Kick-Start Aborted by User.")
            self.force_off()

    async def play_melody(self, notes):
        async with self.buzzer_lock:
            for freq, duration, pause in notes:
                if freq > 0:
                    self.buzzer.freq(int(freq))
                    self.buzzer.duty_u16(BUZZER_VOLUME)
                else:
                    self.buzzer.duty_u16(0)
                await asyncio.sleep(duration)
                self.buzzer.duty_u16(0)
                if pause > 0:
                    await asyncio.sleep(pause)

    async def beep_startup(self):
        await self.play_melody(
            [(523, 0.02, 0.01), (659, 0.02, 0.01), (784, 0.02, 0.01), (1047, 0.04, 0)]
        )

    async def beep_cooler_slow(self):
        await self.play_melody([(659, 0.02, 0.01), (880, 0.04, 0)])

    async def beep_cooler_fast(self):
        await self.play_melody([(659, 0.02, 0.01), (880, 0.02, 0.01), (1318, 0.04, 0)])

    async def beep_cooler_off(self):
        await self.play_melody([(880, 0.02, 0.01), (659, 0.04, 0)])

    async def beep_denied(self):
        await self.play_melody([(300, 0.04, 0.02), (300, 0.05, 0)])

    async def beep_learn_enter(self):
        await self.play_melody(
            [(600, 0.02, 0.01), (800, 0.02, 0.01), (1000, 0.02, 0.01), (1200, 0.04, 0)]
        )

    async def beep_learn_exit(self):
        await self.play_melody(
            [(1200, 0.02, 0.01), (1000, 0.02, 0.01), (800, 0.02, 0.01), (600, 0.04, 0)]
        )

    async def beep_card_added(self):
        await self.play_melody([(1047, 0.03, 0.01), (1568, 0.05, 0)])

    async def beep_card_removed(self):
        await self.play_melody([(1047, 0.03, 0.01), (523, 0.05, 0)])


def _notify_status():
    global _cloud
    if _cloud:
        asyncio.create_task(_cloud.push_status())


def _notify_scan(uid, action):
    global _cloud
    if _cloud:
        asyncio.create_task(_cloud.push_scan(uid, action))


# ==========================================
# 4. ONLINE TASKS
# ==========================================
def _save_wifi_to_config(ssid, password):
    cfg = load_config()
    cfg["wifi_ssid"] = ssid or ""
    cfg["wifi_pass"] = password or ""
    try:
        with open(CONFIG_FILE, "w") as f:
            json.dump(cfg, f)
        print("[CFG] WiFi saved")
    except Exception as e:
        print("[CFG] WiFi save failed:", e)


async def cloud_session_loop(cfg, wifi, cloud):
    from ws_client import AsyncWSClient

    host = cfg.get("server_host", "")
    port = int(cfg.get("server_port", 443))
    use_ssl = bool(cfg.get("use_ssl", True))
    ws_path = cfg.get("ws_path", "/ws/hardware")
    token = cfg.get("hardware_token", "")
    device_id = cfg.get("device_id", "")
    role = cfg.get("device_role", "cooler")

    sep = "&" if "?" in ws_path else "?"
    path = "{}{}token={}&role={}&device_id={}".format(
        ws_path, sep, token, role, device_id
    )

    backoff = 2
    while True:
        try:
            if not wifi.is_connected():
                await asyncio.sleep(2)
                continue
            ws = AsyncWSClient(host, port, path, use_ssl=use_ssl)
            ok = await ws.connect()
            if not ok:
                await asyncio.sleep(backoff)
                backoff = min(backoff * 2, 60)
                continue
            backoff = 2
            cloud.attach_ws(ws, device_id, role)
            await cloud.drain_outbox()
            await cloud.push_status()
            last_ping = time.ticks_ms()
            while ws.open:
                if time.ticks_diff(time.ticks_ms(), last_ping) > 15000:
                    await ws.send_json({"type": "ping"})
                    last_ping = time.ticks_ms()
                try:
                    msg = await asyncio.wait_for(ws.recv(), timeout=1.0)
                except asyncio.TimeoutError:
                    msg = None
                if msg:
                    await cloud.handle_command(msg)
            cloud.attach_ws(None, device_id, role)
            await asyncio.sleep(backoff)
            backoff = min(backoff * 2, 60)
        except Exception as e:
            print("[CLOUD] Session error:", e)
            await asyncio.sleep(backoff)
            backoff = min(backoff * 2, 60)


# ==========================================
# 5. MAIN ASYNC LOGIC
# ==========================================
async def system_runner():
    global COOLER_STATE, LEARN_MODE, LEARN_MODE_TIMER, _cloud

    try:
        wdt = WDT(timeout=10000)
    except Exception:
        wdt = None

    cfg = load_config()
    hw = HardwareManager()
    authorized_cards = load_cards()

    if MASTER_CARD_UID in authorized_cards:
        authorized_cards.remove(MASTER_CARD_UID)
        save_cards(authorized_cards)

    print("[SYS]", len(authorized_cards), "Cards Loaded.")
    if DEBUG_MODE:
        print("[SYS] DEBUG MODE IS ACTIVE!")

    from cloud import CloudBridge
    from outbox import Outbox

    outbox = Outbox(enabled=bool(cfg.get("outbox_enabled", True)))
    _cloud = CloudBridge(
        hw,
        get_state=lambda: COOLER_STATE,
        set_state=lambda v: _set_cooler_state(v),
        get_learn=lambda: LEARN_MODE,
        outbox=outbox,
    )
    _cloud.device_id = cfg.get("device_id", "")
    _cloud.device_role = cfg.get("device_role", "cooler")

    wifi = None
    online_enabled = bool(cfg.get("online_enabled", False))
    if online_enabled and cfg.get("wifi_ssid") and cfg.get("server_host"):
        try:
            from wifi_manager import WifiManager

            wifi = WifiManager(cfg.get("wifi_ssid", ""), cfg.get("wifi_pass", ""))
            asyncio.create_task(wifi.ensure_loop())
            asyncio.create_task(cloud_session_loop(cfg, wifi, _cloud))
            print("[SYS] Online dual-mode enabled")
        except Exception as e:
            print("[SYS] Online init failed; staying offline:", e)
    else:
        print("[SYS] Cloud WSS disabled")

    # SoftAP + captive DNS: immediate if enabled/no SSID; else after STA fail streak
    ap_enabled = bool(cfg.get("ap_enabled", False))
    setup_mode = not bool(cfg.get("wifi_ssid"))
    need_ap = ap_enabled or setup_mode
    ap_state = {"mgr": None, "ok": False}
    rf_ref = {"learner": None}
    wifi_ref = {"mgr": wifi}

    async def _start_softap(reason, disable_sta=False):
        if ap_state["ok"]:
            return
        try:
            from ap_manager import ApManager
            from dns_captive import CaptiveDns

            device_id = cfg.get("device_id", "cooler")
            ap = ApManager(
                "Cooler-{}".format(device_id[-8:]),
                str(cfg.get("local_pin", "1234")),
            )
            # Setup (no SSID): disable STA so SoftAP is clean; STA-fail keeps STA radio
            if ap.start(disable_sta=disable_sta):
                ap_state["mgr"] = ap
                asyncio.create_task(CaptiveDns(ap.ip()).run())
                ap_state["ok"] = True
                print("[SYS] SoftAP started (%s) PSK=local_pin" % reason)
        except Exception as e:
            print("[SYS] AP init failed:", e)

    def _stop_softap(reason):
        mgr = ap_state.get("mgr")
        if mgr and ap_state["ok"]:
            try:
                mgr.stop()
            except Exception as e:
                print("[SYS] AP stop error:", e)
            ap_state["ok"] = False
            ap_state["mgr"] = None
            print("[SYS] SoftAP stopped (%s)" % reason)

    if need_ap:
        await _start_softap("boot", disable_sta=setup_mode)

    async def ap_lifecycle_loop():
        """Start SoftAP on STA fail; tear down SoftAP once STA is healthy again."""
        fails = 0
        while True:
            try:
                await asyncio.sleep(5)
                w = wifi_ref.get("mgr")
                if w and w.is_connected():
                    fails = 0
                    if ap_state["ok"] and not setup_mode:
                        _stop_softap("sta_ok")
                    continue
                if not ap_enabled and not setup_mode:
                    continue
                if ap_state["ok"]:
                    continue
                fails += 1
                if fails >= 6:
                    await _start_softap("sta_fail", disable_sta=False)
                    fails = 0
            except Exception as e:
                print("[SYS] AP lifecycle error:", e)
                await asyncio.sleep(5)

    if ap_enabled or setup_mode:
        asyncio.create_task(ap_lifecycle_loop())

    def _on_wifi_saved(ssid, password):
        """Persist already done; kick STA reconnect and prefer STA over AP."""
        try:
            from wifi_manager import WifiManager

            if wifi_ref["mgr"] is None:
                wifi_ref["mgr"] = WifiManager(ssid or "", password or "")
                asyncio.create_task(wifi_ref["mgr"].ensure_loop())
                if online_enabled and cfg.get("server_host"):
                    asyncio.create_task(
                        cloud_session_loop(cfg, wifi_ref["mgr"], _cloud)
                    )
            else:
                wifi_ref["mgr"].ssid = ssid or ""
                wifi_ref["mgr"].password = password or ""
                wifi_ref["mgr"].connect_once()
            print("[SYS] WiFi reconnect requested after portal save")
        except Exception as e:
            print("[SYS] WiFi reconnect failed:", e)

    # Local HTTP on AP/STA (PIN-gated); channel http_ap vs http_local decided per request
    if bool(cfg.get("lan_http_enabled", True)) or need_ap or ap_enabled:
        try:
            from local_http import LocalHttpServer

            http = LocalHttpServer(
                apply_mode=_cloud.apply_mode,
                cycle=_cloud.cycle,
                get_state=lambda: COOLER_STATE,
                get_learn=lambda: LEARN_MODE,
                local_pin=cfg.get("local_pin", "1234"),
                save_wifi=_save_wifi_to_config,
                channel="http_local",
                rf_learn=lambda slot: rf_ref["learner"].enter_learn(slot)
                if rf_ref["learner"]
                else None,
                on_wifi_saved=_on_wifi_saved,
            )
            asyncio.create_task(http.start("0.0.0.0", 80))
        except Exception as e:
            print("[SYS] Local HTTP failed:", e)

    if bool(cfg.get("wall_enabled", False)):
        try:
            from wall_inputs import WallInputs

            wall = WallInputs(
                apply_mode=_cloud.apply_mode,
                pin_map={
                    0: int(cfg.get("wall_pin_off", 33)),
                    1: int(cfg.get("wall_pin_slow", 14)),
                    2: int(cfg.get("wall_pin_fast", 15)),
                },
            )
            asyncio.create_task(wall.poll_loop())
            print("[SYS] Wall inputs enabled")
        except Exception as e:
            print("[SYS] Wall inputs failed:", e)

    if bool(cfg.get("rf433_enabled", False)):
        try:
            from rf433 import Rf433Learner

            rf = Rf433Learner(
                pin=int(cfg.get("rf433_pin", 27)),
                apply_mode=_cloud.apply_mode,
                cycle=_cloud.cycle,
            )
            rf_ref["learner"] = rf
            asyncio.create_task(rf.poll_loop())
            print("[SYS] RF433 enabled")
        except Exception as e:
            print("[SYS] RF433 failed:", e)

    if bool(cfg.get("ble_enabled", False)):
        try:
            from ble_control import BleControl

            ble = BleControl(
                apply_mode=_cloud.apply_mode,
                cycle=_cloud.cycle,
                get_state=lambda: COOLER_STATE,
                pin=str(cfg.get("ble_pin", cfg.get("local_pin", "1234"))),
                name="Cooler-{}".format(cfg.get("device_id", "001")[-8:]),
            )
            asyncio.create_task(ble.run())
            print("[SYS] BLE enabled")
        except Exception as e:
            print("[SYS] BLE failed:", e)

    if bool(cfg.get("sms_uart_enabled", False)):
        try:
            from sms_modem import SmsModem

            sms = SmsModem(
                tx=int(cfg.get("sms_uart_tx", 26)),
                rx=int(cfg.get("sms_uart_rx", 25)),
                pin=str(cfg.get("sms_pin", cfg.get("local_pin", "1234"))),
                apply_mode=_cloud.apply_mode,
                cycle=_cloud.cycle,
            )
            asyncio.create_task(sms.poll_loop())
            print("[SYS] SMS UART enabled")
        except Exception as e:
            print("[SYS] SMS UART failed:", e)

    if bool(cfg.get("mqtt_enabled", False)) and cfg.get("mqtt_host"):
        try:
            from mqtt_client import MqttCooler

            mqtt = MqttCooler(
                host=cfg.get("mqtt_host", ""),
                port=int(cfg.get("mqtt_port", 1883)),
                prefix=cfg.get("mqtt_topic_prefix", "cooler"),
                device_id=cfg.get("device_id", "cooler"),
                apply_mode=_cloud.apply_mode,
                cycle=_cloud.cycle,
                get_state=lambda: COOLER_STATE,
            )
            asyncio.create_task(mqtt.run())
            print("[SYS] MQTT enabled")
        except Exception as e:
            print("[SYS] MQTT failed:", e)

    asyncio.create_task(hw.beep_startup())

    last_scanned_uid = ""
    last_scanned_time = time.ticks_ms()
    rfid_error_count = 0

    is_master_held = False
    master_hold_start = 0
    master_last_seen = 0
    long_press_executed = False

    while True:
        if wdt:
            wdt.feed()

        now = time.ticks_ms()

        if LEARN_MODE and time.ticks_diff(now, LEARN_MODE_TIMER) > 15000:
            LEARN_MODE = False
            print("[SYS] Exit Learn Mode (Timeout)")
            asyncio.create_task(hw.beep_learn_exit())
            _notify_status()

        # Master release detection (short tap vs long press)
        if is_master_held and time.ticks_diff(now, master_last_seen) > 1500:
            if not long_press_executed:
                # Short tap on release
                if LEARN_MODE:
                    LEARN_MODE = False
                    print("[SYS] EXIT LEARN MODE (MASTER SHORT TAP)")
                    asyncio.create_task(hw.beep_learn_exit())
                    _notify_scan(MASTER_CARD_UID, "learn_exit")
                    _notify_status()
                else:
                    print("[RFID] Master short tap -> cycle")
                    COOLER_STATE = (COOLER_STATE + 1) % 3
                    hw.change_mode(COOLER_STATE)
                    if COOLER_STATE == 1:
                        asyncio.create_task(hw.beep_cooler_slow())
                    elif COOLER_STATE == 2:
                        asyncio.create_task(hw.beep_cooler_fast())
                    else:
                        asyncio.create_task(hw.beep_cooler_off())
                    _notify_scan(MASTER_CARD_UID, "cycle")
                    _notify_status()
            is_master_held = False
            long_press_executed = False

        if hw.rdr:
            try:
                (stat, tag_type) = hw.rdr.request(hw.rdr.REQIDL)
                if stat == hw.rdr.OK:
                    (stat, uid) = hw.rdr.anticoll()
                    if stat == hw.rdr.OK:
                        rfid_error_count = 0
                        uid_str = "0x%02x%02x%02x%02x" % (
                            uid[0],
                            uid[1],
                            uid[2],
                            uid[3],
                        )

                        if uid_str == MASTER_CARD_UID:
                            master_last_seen = now
                            if not is_master_held:
                                is_master_held = True
                                master_hold_start = now
                                long_press_executed = False

                            if (
                                not long_press_executed
                                and time.ticks_diff(now, master_hold_start)
                                > MASTER_HOLD_TIME
                            ):
                                long_press_executed = True
                                if not LEARN_MODE:
                                    LEARN_MODE = True
                                    LEARN_MODE_TIMER = now
                                    print("\n[SYS] ENTER LEARN MODE (LONG PRESS)")
                                    COOLER_STATE = 0
                                    hw.change_mode(0)
                                    asyncio.create_task(hw.beep_learn_enter())
                                    _notify_scan(uid_str, "learn_enter")
                                    _notify_status()
                                else:
                                    LEARN_MODE = False
                                    print("\n[SYS] EXIT LEARN MODE (LONG PRESS)")
                                    asyncio.create_task(hw.beep_learn_exit())
                                    _notify_scan(uid_str, "learn_exit")
                                    _notify_status()
                            # Never run immediate cycle for master
                            continue

                        # Debounce for non-master cards
                        if (
                            uid_str == last_scanned_uid
                            and time.ticks_diff(now, last_scanned_time) < 1500
                        ):
                            continue

                        last_scanned_uid = uid_str
                        last_scanned_time = now
                        print("\n[RFID] Scanned:", uid_str)

                        if LEARN_MODE:
                            action = toggle_card(uid_str)
                            authorized_cards = load_cards()
                            if action == "ADDED":
                                print("[SYS] CARD ADDED:", uid_str)
                                asyncio.create_task(hw.beep_card_added())
                                _notify_scan(uid_str, "learn_add")
                            else:
                                print("[SYS] CARD REMOVED:", uid_str)
                                asyncio.create_task(hw.beep_card_removed())
                                _notify_scan(uid_str, "learn_remove")
                            LEARN_MODE_TIMER = now
                        else:
                            if (
                                uid_str in authorized_cards
                                or DEBUG_MODE
                            ):
                                COOLER_STATE = (COOLER_STATE + 1) % 3
                                hw.change_mode(COOLER_STATE)
                                if COOLER_STATE == 1:
                                    asyncio.create_task(hw.beep_cooler_slow())
                                elif COOLER_STATE == 2:
                                    asyncio.create_task(hw.beep_cooler_fast())
                                else:
                                    asyncio.create_task(hw.beep_cooler_off())
                                _notify_scan(uid_str, "cycle")
                                _notify_status()
                            else:
                                print("[HW] Access Denied!")
                                asyncio.create_task(hw.beep_denied())
                                _notify_scan(uid_str, "denied")

            except Exception as e:
                rfid_error_count += 1
                if rfid_error_count > 5:
                    print("[RFID] Multiple Read Errors. Auto-Recovering SPI...", e)
                    hw.init_rfid()
                    rfid_error_count = 0

        gc.collect()
        await asyncio.sleep(0.05)


def _set_cooler_state(v):
    global COOLER_STATE
    COOLER_STATE = v


if __name__ == "__main__":
    try:
        asyncio.run(system_runner())
    except KeyboardInterrupt:
        print("Stopped by User")
    except Exception as e:
        print("CRITICAL ERROR:", e)
        time.sleep(1)
        machine.reset()
