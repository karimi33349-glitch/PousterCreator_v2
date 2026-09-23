نسخه اصلاح‌شده برای APK

اصلاحات:
- حذف Page.get_assets_path()
- استفاده از FLET_ASSETS_DIR برای assets در APK
- fallback به assets کنار main.py در اجرای محلی
- استفاده از FLET_APP_STORAGE_DATA برای output قابل‌نوشتن و پایدار
- ft.run(main, assets_dir="assets") برای ثبت assets

فایل‌های واقعی زیر باید در assets قرار بگیرند:
- template.jpg
- calibrib.ttf
