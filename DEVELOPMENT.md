# PousterCreator v6 — Development Package

این بسته از فایل‌های واقعی موجود در APK نسخه v6 بازسازی شده است.
فایل‌های لازم برای ادامه توسعه در آن قرار گرفته‌اند:

- `main.py` — سورس برنامه
- `requirements.txt` — وابستگی‌های Python
- `pyproject.toml` — تنظیمات Flet
- `assets/template.jpg` — قالب اصلی پوستر
- `assets/calibrib.ttf` — فونت فارسی
- `assets/icon.png` — آیکون برنامه
- `.github/workflows/apk-build.yml` — ساخت APK در GitHub Actions
- `README.md` و `README.txt` — مستندات موجود پروژه
- `.gitignore`

## اجرای ویندوز

Python 3.12 پیشنهاد می‌شود.

```bash
python -m venv .venv
.venv\\Scripts\\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
flet run main.py
```

## ساخت APK

Workflow گیت‌هاب داخل:

`.github/workflows/apk-build.yml`

قرار دارد.

## نکته درباره مدل حذف پس‌زمینه

این نسخهٔ توسعه، دقیقاً بر اساس سورسی است که داخل APK v6 ذخیره شده بود. در آن نسخه، فایل مدل ONNX حذف پس‌زمینه داخل پروژه/بستهٔ source وجود ندارد.
اگر قرار است قابلیت حذف پس‌زمینه نیز به همین نسخه افزوده شود، مدل و وابستگی‌های آن باید جداگانه به پروژه اضافه شوند.
