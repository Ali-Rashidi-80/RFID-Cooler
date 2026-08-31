# میرورهای ایرانی (اولویت ملی) — Cooler / SentryGate

**زبان‌ها:** [English](IRAN_MIRRORS.md) · **فارسی**

در اختلال اینترنت بین‌الملل یا شبکهٔ ملی، **همیشه ابتدا** از میرور چابکان استفاده شود.

## چابکان (`mirror2.chabokan.net`)

| سرویس | آدرس |
|--------|------|
| NPM | `https://mirror2.chabokan.net/npm/` |
| PyPI | `https://mirror2.chabokan.net/pypi/simple/` |
| Docker | `docker pull mirror2.chabokan.net/<image>` یا `registry-mirrors` |
| APT (Debian/Ubuntu) | طبق راهنمای [iran.chabokan.net](https://iran.chabokan.net/) |

### NPM (cooler-web / frontend)

```bash
npm config set registry https://mirror2.chabokan.net/npm/
# یا فایل .npmrc داخل پروژه (از قبل تنظیم شده در cooler-web)
npm install --legacy-peer-deps
```

### PyPI (backend)

```bash
pip install --index-url https://mirror2.chabokan.net/pypi/simple/ --trusted-host mirror2.chabokan.net -r requirements.txt
```

فایل نمونه: `door_control/backend/pip.conf`

### Docker

```json
{
  "registry-mirrors": ["https://mirror2.chabokan.net"]
}
```

Composeهای `door_control` از پیش با پیشوند `mirror2.chabokan.net/...` تنظیم شده‌اند.

### MicroPython / mip

چابکان ایندکس اختصاصی mip ندارد. برای ایران:

1. پکیج‌ها را روی PC از میرور/کَش داخلی دانلود کنید
2. با `mpremote fs cp` روی دستگاه کپی کنید  
یا یک `package.json` استاتیک روی سرور داخلی/چابکان میزبانی کنید.

## اولویت‌بندی رجیستری (پیشنهاد مهندسی)

1. Chabokan mirror2  
2. سایر میرورهای داخل کشور (آروان / لیارا / …) در صورت نیاز  
3. رجیستری عمومی فقط وقتی ۱ و ۲ در دسترس نیستند
