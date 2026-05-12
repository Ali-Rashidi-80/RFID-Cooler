# ==================== MicroPython ====================
# برای ESP32 / ESP8266 / Raspberry Pi Pico
# ماژول SSR: A03B 5V 1-Channel (Active Low + AC-only)
# بار: قفل زنجیری ۱۲ ولت DC (solenoid فنردار)

from machine import Pin
from time import sleep_ms, sleep


RELAY_PIN = 16        # پین GPIO که به CH1 ماژول SSR وصل کردی


relay = Pin(RELAY_PIN, Pin.OUT)


# وضعیت ایمن در شروع: حتماً رله خاموش باشد
relay.value(1)   # HIGH = خاموش (Active Low)


def safe_open_lock(duration_ms=600):
    """
    باز کردن قفل به صورت کاملاً ایمن
    مدت زمان پیشنهادی: 500 تا 800 میلی‌ثانیه
    600 میلی‌ثانیه برای ۹۹٪ قفل‌های زنجیری ایرانی عالیه
    """
    print("قفل در حال باز شدن...")

    
    relay.value(0)            # رله روشن (LOW)
    sleep_ms(duration_ms)     # پالس دقیق
    relay.value(1)            # دستور خاموش کردن (حتی اگر کمی دیر خاموش بشه مهم نیست)
    
    # تضمین اضافی: ۱۰۰ میلی‌ثانیه صبر کنیم تا مطمئن شویم فنر قفل برگشته
    sleep_ms(100)
    
    print("قفل دوباره بسته شد ✓")

# ───── تابع تست سریع (برای اولین بار اجراش کن) ─────
def test_lock(times=10):
    print("شروع تست {} باره‌ای...".format(times))
    for i in range(times):
        print("تست شماره", i+1)
        safe_open_lock(600)
        sleep(3)   # فاصله بین تست‌ها

# ───── استفاده اصلی ─────
# فقط این تابع رو هرجا که خواستی صدا بزن (دکمه، وب، تلگرام، RFID و ...)
# مثال:
# safe_open_lock(600)   # ۶۰۰ میلی‌ثانیه پالس

# ───── اجرای تست هنگام روشن شدن بورد (حذفش کن بعد از اولین تست موفق) ─────
if __name__ == "__main__":
    sleep(2)  # ۲ ثانیه صبر تا سریال وصل بشه
    print("قفل زنجیری ۱۲ ولت با SSR AC-only — نسخه نهایی ایمن")
    test_lock(5)   # فقط ۵ بار تست کنه، بعدش کامنتش کن