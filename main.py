# Ali Rashidi
# t.me/WriteYourway

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

CARDS_FILE = 'cards.json'
TMP_FILE = 'cards.tmp'

BUZZER_VOLUME = 120 

COOLER_STATE = 0      
LEARN_MODE = False    
LEARN_MODE_TIMER = 0  

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

# ==========================================
# 2. BULLETPROOF CARD MANAGEMENT
# ==========================================
def load_cards():
    try:
        with open(CARDS_FILE, 'r') as f:
            return json.load(f)
    except Exception:
        try:
            with open(TMP_FILE, 'r') as f:
                return json.load(f)
        except Exception:
            return [] 

def save_cards(cards):
    try:
        with open(TMP_FILE, 'w') as f:
            json.dump(cards, f)
        try:
            os.remove(CARDS_FILE)
        except OSError:
            pass
        os.rename(TMP_FILE, CARDS_FILE)
    except Exception as e:
        print(f"[SYS] Error saving cards: {e}")

def toggle_card(uid):
    cards = load_cards()
    if uid in cards:
        cards.remove(uid)
        save_cards(cards)
        return "REMOVED"
    else:
        cards.append(uid)
        save_cards(cards)
        return "ADDED"

# ==========================================
# 3. HARDWARE MANAGER (Task Cancellation Architecture)
# ==========================================
class HardwareManager:
    def __init__(self):
        self.relay_main = machine.Pin(PIN_RELAY_MAIN_SSR, machine.Pin.OUT)
        self.relay_speed = machine.Pin(PIN_RELAY_SPEED_MECH, machine.Pin.OUT)
        
        self.current_task = None # متغیر ذخیره تسک در حال اجرا برای لغو در صورت نیاز
        self.force_off() 
        
        self.buzzer = PWM(Pin(PIN_BUZZER))
        self.buzzer.duty_u16(0)
        self.buzzer_lock = asyncio.Lock() 
        
        self.init_rfid()

    def init_rfid(self):
        try:
            rst = Pin(RST_PIN, Pin.OUT)
            rst.off(); time.sleep(0.05)
            rst.on(); time.sleep(0.05)
            self.spi = SPI(1, baudrate=2500000, polarity=0, phase=0, sck=Pin(SCK_PIN), mosi=Pin(MOSI_PIN), miso=Pin(MISO_PIN))
            self.rdr = MFRC522(spi=self.spi, cs=Pin(CS_PIN, Pin.OUT))
            print("[HW] RFID Initialized & Ready")
            return True
        except Exception as e:
            print(f"[HW] RFID Init Error: {e}")
            self.rdr = None
            return False

    def force_off(self):
        # رله‌ها Active-Low هستند (1=OFF | 0=ON)
        self.relay_main.value(1)  
        self.relay_speed.value(1)

    # 🛡️ مدیر یکپارچه وظایف (جلوگیری از تداخل دستورات) 🛡️
    def change_mode(self, mode):
        # اگر تسکی (مثل کیک‌استارت) در حال اجراست، فوراً آن را کُشته و متوقف کن
        if self.current_task:
            self.current_task.cancel()
            
        if mode == 0:
            self.current_task = asyncio.create_task(self._task_off())
        elif mode == 1:
            self.current_task = asyncio.create_task(self._task_slow())
        elif mode == 2:
            self.current_task = asyncio.create_task(self._task_fast())

    # 🛑 خاموشی ایمن
    async def _task_off(self):
        try:
            self.relay_main.value(1) # قطع کامل برق اصلی
            await asyncio.sleep(0.1) # استراحت
            self.relay_speed.value(1) # استراحت رله مکانیکی
            print("[COOLER] OFF")
        except asyncio.CancelledError:
            pass

    # 🚀 دور تند ایمن
    async def _task_fast(self):
        try:
            self.relay_main.value(1) # قطع برق اصلی
            await asyncio.sleep(0.1)
            self.relay_speed.value(0) # سوئیچ به دور تند (بدون جرقه)
            await asyncio.sleep(0.05)
            self.relay_main.value(0) # وصل برق
            print("[COOLER] ON - FAST")
        except asyncio.CancelledError:
            pass

    # 🐌 دور کند با کیک‌استارت 3 ثانیه‌ای ایمن
    async def _task_slow(self):
        try:
            print("[COOLER] ON - SLOW (KICK-STARTING IN FAST FOR 3s...)")
            
            # ۱. استارت اولیه با دور تند (برای غلبه بر اینرسی موتور)
            self.relay_main.value(1)
            await asyncio.sleep(0.1)
            self.relay_speed.value(0) # تنظیم روی تند
            await asyncio.sleep(0.05)
            self.relay_main.value(0) # روشن شدن موتور روی دور تند
            
            # ۲. سه ثانیه صبر آسنکرون (اگر کاربر کارت بزند، تسک همینجا کُشته می‌شود)
            await asyncio.sleep(3)
            
            # ۳. پایان 3 ثانیه -> انتقال ایمن (Dry Switch) به دور کند
            print("[COOLER] KICK-START DONE. SWITCHING TO SLOW SAFELY...")
            self.relay_main.value(1)  # قطع برق برای جلوگیری از جرقه رله
            await asyncio.sleep(0.1)  # تخلیه بار سلفی موتور
            self.relay_speed.value(1) # تغییر فیزیکی رله مکانیکی به دور کند
            await asyncio.sleep(0.05) # نشستن پلاتین
            self.relay_main.value(0)  # وصل مجدد برق
            
        except asyncio.CancelledError:
            # اگر کاربر قبل از 3 ثانیه کارت جدیدی بزند، کیک‌استارت با آرامش لغو می‌شود
            print("[COOLER] Kick-Start Aborted by User.")

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

    # --- 🚀 THEMATIC MELODIES (EXTREME ULTRA-FAST) 🚀 ---
    async def beep_startup(self):
        await self.play_melody([(523, 0.02, 0.01), (659, 0.02, 0.01), (784, 0.02, 0.01), (1047, 0.04, 0)])
    async def beep_cooler_slow(self):
        await self.play_melody([(659, 0.02, 0.01), (880, 0.04, 0)])
    async def beep_cooler_fast(self):
        await self.play_melody([(659, 0.02, 0.01), (880, 0.02, 0.01), (1318, 0.04, 0)])
    async def beep_cooler_off(self):
        await self.play_melody([(880, 0.02, 0.01), (659, 0.04, 0)])
    async def beep_denied(self):
        await self.play_melody([(300, 0.04, 0.02), (300, 0.05, 0)])
    async def beep_learn_enter(self):
        await self.play_melody([(600, 0.02, 0.01), (800, 0.02, 0.01), (1000, 0.02, 0.01), (1200, 0.04, 0)])
    async def beep_learn_exit(self):
        await self.play_melody([(1200, 0.02, 0.01), (1000, 0.02, 0.01), (800, 0.02, 0.01), (600, 0.04, 0)])
    async def beep_card_added(self):
        await self.play_melody([(1047, 0.03, 0.01), (1568, 0.05, 0)])
    async def beep_card_removed(self):
        await self.play_melody([(1047, 0.03, 0.01), (523, 0.05, 0)])

# ==========================================
# 4. MAIN ASYNC LOGIC
# ==========================================
async def system_runner():
    global COOLER_STATE, LEARN_MODE, LEARN_MODE_TIMER
    
    try:
        wdt = WDT(timeout=10000)
    except:
        wdt = None

    hw = HardwareManager()
    authorized_cards = load_cards()
    
    if MASTER_CARD_UID in authorized_cards:
        authorized_cards.remove(MASTER_CARD_UID)
        save_cards(authorized_cards)

    print(f"[SYS] {len(authorized_cards)} Cards Loaded.")
    if DEBUG_MODE:
        print("[SYS] ⚠️ DEBUG MODE IS ACTIVE!")
        
    asyncio.create_task(hw.beep_startup()) 

    last_scanned_uid = ""
    last_scanned_time = time.ticks_ms()
    rfid_error_count = 0 
    
    is_master_held = False
    master_hold_start = 0
    master_last_seen = 0
    long_press_executed = False

    while True:
        if wdt: wdt.feed()
        
        now = time.ticks_ms()

        # تایمر خروج از حالت یادگیری
        if LEARN_MODE and time.ticks_diff(now, LEARN_MODE_TIMER) > 15000:
            LEARN_MODE = False
            print("[SYS] Exit Learn Mode (Timeout)")
            asyncio.create_task(hw.beep_learn_exit())

        # بررسی قطع ارتباط کارت مستر
        if is_master_held and time.ticks_diff(now, master_last_seen) > 1500:
            is_master_held = False
            long_press_executed = False

        if hw.rdr:
            try:
                (stat, tag_type) = hw.rdr.request(hw.rdr.REQIDL)
                if stat == hw.rdr.OK:
                    (stat, uid) = hw.rdr.anticoll()
                    if stat == hw.rdr.OK:
                        rfid_error_count = 0 
                        uid_str = "0x%02x%02x%02x%02x" % (uid[0], uid[1], uid[2], uid[3])
                        
                        # 1. منطق Long Press (انحصاری کارت مستر)
                        if uid_str == MASTER_CARD_UID:
                            master_last_seen = now
                            if not is_master_held:
                                is_master_held = True
                                master_hold_start = now
                                long_press_executed = False
                            
                            if not long_press_executed and time.ticks_diff(now, master_hold_start) > MASTER_HOLD_TIME:
                                long_press_executed = True
                                
                                if not LEARN_MODE:
                                    LEARN_MODE = True
                                    LEARN_MODE_TIMER = now 
                                    print("\n[SYS] ENTER LEARN MODE (LONG PRESS HELD)")
                                    COOLER_STATE = 0 
                                    hw.change_mode(0) # خاموشی فوق‌العاده امن (Cancel Task + Dry Switch)
                                    asyncio.create_task(hw.beep_learn_enter())
                                else:
                                    LEARN_MODE = False
                                    print("\n[SYS] EXIT LEARN MODE (LONG PRESS HELD)")
                                    asyncio.create_task(hw.beep_learn_exit())
                        
                        # 2. منطق Debounce ترکیبی
                        if uid_str == last_scanned_uid and time.ticks_diff(now, last_scanned_time) < 1500:
                            if uid_str == MASTER_CARD_UID:
                                last_scanned_time = now
                            continue

                        # 3. اجرای اکشن کارت
                        last_scanned_uid = uid_str
                        last_scanned_time = now
                        print(f"\n[RFID] Scanned: {uid_str}")

                        if LEARN_MODE:
                            if uid_str == MASTER_CARD_UID:
                                LEARN_MODE = False
                                print("[SYS] EXIT LEARN MODE (MASTER CARD SHORT TAP)")
                                asyncio.create_task(hw.beep_learn_exit())
                            else:
                                action = toggle_card(uid_str)
                                authorized_cards = load_cards() 
                                if action == "ADDED":
                                    print(f"[SYS] CARD ADDED: {uid_str}")
                                    asyncio.create_task(hw.beep_card_added())
                                else:
                                    print(f"[SYS] CARD REMOVED: {uid_str}")
                                    asyncio.create_task(hw.beep_card_removed())
                                
                                LEARN_MODE_TIMER = now 
                                
                        else:
                            # ⚙️ حالت عادی کنترل کولر ⚙️
                            if uid_str in authorized_cards or DEBUG_MODE or uid_str == MASTER_CARD_UID:
                                COOLER_STATE = (COOLER_STATE + 1) % 3
                                
                                # کانال امن برای تغییر وضعیت رله‌ها همراه با لغو تسک‌های قبلی
                                hw.change_mode(COOLER_STATE)
                                
                                if COOLER_STATE == 1:
                                    asyncio.create_task(hw.beep_cooler_slow())
                                elif COOLER_STATE == 2:
                                    asyncio.create_task(hw.beep_cooler_fast())
                                else:
                                    asyncio.create_task(hw.beep_cooler_off())
                            else:
                                print("[HW] Access Denied!")
                                asyncio.create_task(hw.beep_denied())

            except Exception as e:
                rfid_error_count += 1
                if rfid_error_count > 5:
                    print(f"[RFID] Multiple Read Errors. Auto-Recovering SPI... ({e})")
                    hw.init_rfid()
                    rfid_error_count = 0
                
        gc.collect()
        await asyncio.sleep(0.05)

if __name__ == "__main__":
    try:
        asyncio.run(system_runner())
    except KeyboardInterrupt:
        print("Stopped by User")
    except Exception as e:
        print(f"CRITICAL ERROR: {e}")
        time.sleep(1)
        machine.reset()