# MicroPython MANUAL HW LAB — buzzer melody sketch only.
# NOT a cooler firmware test (see main.py HardwareManager for product audio UI).
from machine import Pin, PWM
import time

# --- تنظیمات سخت‌افزار ---
# پین بازر را اینجا مشخص کنید (مثلاً 25 برای Pico/ESP32)
BUZZER_PIN = 17 
buzzer = PWM(Pin(BUZZER_PIN))
buzzer.duty_u16(0) # شروع با سکوت

def sound(freq, duration_ms):
    """تابع کمکی برای تولید صدا با شفافیت بالا (دیوتی سایکل 50%)"""
    if freq < 50: freq = 50
    buzzer.freq(int(freq))
    buzzer.duty_u16(32768) # مقدار 32768 یعنی 50% قدرت (بهترین کیفیت)
    time.sleep_ms(duration_ms)

def silence(duration_ms):
    """تابع ایجاد سکوت"""
    buzzer.duty_u16(0)
    time.sleep_ms(duration_ms)

# ==========================================
# 🎵 بخش 1: صداهای موفقیت (Success)
# ==========================================

def play_success_pro():
    """گزینه 1: مجیک چایم (Magic Chime) - پیشرفته و جذاب"""
    print("✨ پخش موفقیت: Magic Chime")
    # نت‌ها: E5, G#5, B5, E6 (آکورد می ماژور)
    melody = [659, 830, 987, 1318] 
    
    # سه نت اول سریع
    for i in range(3):
        sound(melody[i], 80)
        silence(20)
        
    # نت آخر کشیده و با تاکید
    silence(30)
    sound(melody[3], 300)
    silence(100)


# ==========================================
# ❌ بخش 2: صدای خطا (Error)
# ==========================================

def play_error_system_fail():
    """خطا: شکست سیستم (System Failure) - حس خاموش شدن"""
    print("❌ پخش خطا: System Failure")
    
    # پخش دو نت "ناکوک" (Dissonant) برای ایجاد حس بدی
    sound(440, 150) # نت اول
    sound(311, 300) # نت دوم (فاصله تریتون)
    
    # افکت خاموش شدن موتور (پایین آمدن فرکانس)
    for f in range(311, 50, -15):
        buzzer.freq(int(f))
        time.sleep_ms(5)
    
    silence(200)

# ==========================================
# 🚨 بخش 3: صدای اضطراری (Emergency)
# ==========================================

def play_alarm_police(loops=5):
    """آژیر: پلیسی (Police) - بلند و هشدار دهنده"""
    print("🚨 پخش آژیر: Police")
    
    for _ in range(loops):
        # نت بالا (High)
        buzzer.freq(900) 
        buzzer.duty_u16(32768)
        time.sleep_ms(250) 
        
        # نت پایین (Low)
        buzzer.freq(600)
        buzzer.duty_u16(32768)
        time.sleep_ms(250)
    
    silence(200)

# ==========================================
# ▶️ حلقه اصلی تست (Main Loop)
# ==========================================
try:
    while True:
        # 1. اجرای موفقیت اصلی (پیشرفته)
        play_success_pro()
        time.sleep(2)
        
        
        # 2. اجرای خطا
        play_error_system_fail()
        time.sleep(2)
        
        # 3. اجرای آژیر اضطراری
        play_alarm_police(loops=4)
        time.sleep(3)
        
        print("--- تکرار چرخه ---")

except KeyboardInterrupt:
    silence(0)
    print("\nبرنامه با موفقیت متوقف شد.")