import io
import os
from datetime import date
from pathlib import Path

import flet as ft
from PIL import Image, ImageDraw, ImageFont, ImageOps
import arabic_reshaper
from bidi.algorithm import get_display

# ============================================================
# تنظیمات قالب ۸۴۰×۱۲۶۰
# ============================================================
BOX_TOP_NUMBER = {"x": 387, "y": 170, "w": 270, "h": 70}
BOX_TOP_TITLE = {"x": 390, "y": 280, "w": 400, "h": 90}
BOX_MIDDLE = {"x": 390, "y": 600, "w": 450, "h": 140}
BOX_PHOTO = {"x": 260, "y": 883, "w": 140, "h": 184}
BOX_PRESENTER = {"x": 465, "y": 895, "w": 210, "h": 90}
BOX_DATE = {"x": 394, "y": 1054, "w": 200, "h": 40}

# ============================================================
# رنگ‌ها
# ============================================================
BG = "#071713"
PANEL = "#10231E"
PANEL_2 = "#172F29"
GOLD = "#D4AF37"
CREAM = "#FDF6E3"
NAVY = "#1A2E2A"
MUTED = "#91A39C"
DANGER = "#D96C6C"
SUCCESS = "#86C99A"
BORDER = "#29463E"

WEEKDAYS = [
    "دوشنبه",
    "سه‌شنبه",
    "چهارشنبه",
    "پنجشنبه",
    "جمعه",
    "شنبه",
    "یکشنبه",
]
JALALI_MONTHS = [
    "فروردین",
    "اردیبهشت",
    "خرداد",
    "تیر",
    "مرداد",
    "شهریور",
    "مهر",
    "آبان",
    "آذر",
    "دی",
    "بهمن",
    "اسفند",
]
PERSIAN_DIGITS = str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹")
ALLOWED_IMAGE_FORMATS = {"JPEG", "PNG", "WEBP"}


# ============================================================
# تاریخ شمسی — بدون وابستگی اضافه
# ============================================================
def gregorian_to_jalali(gy: int, gm: int, gd: int):
    g_days_in_month = [0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334]

    if gy > 1600:
        jy = 979
        gy2 = gy - 1600
    else:
        jy = 0
        gy2 = gy - 621

    gy3 = gy2 + 1 if gm > 2 else gy2
    days = (
            365 * gy2
            + (gy3 + 3) // 4
            - (gy3 + 99) // 100
            + (gy3 + 399) // 400
            - 80
            + gd
            + g_days_in_month[gm - 1]
    )

    jy += 33 * (days // 12053)
    days %= 12053
    jy += 4 * (days // 1461)
    days %= 1461

    if days > 365:
        jy += (days - 1) // 365
        days = (days - 1) % 365

    if days < 186:
        jm = 1 + days // 31
        jd = 1 + days % 31
    else:
        jm = 7 + (days - 186) // 30
        jd = 1 + (days - 186) % 30

    return jy, jm, jd


def to_persian_digits(value) -> str:
    return str(value).translate(PERSIAN_DIGITS)


def today_jalali_text() -> str:
    now = date.today()
    jy, jm, jd = gregorian_to_jalali(now.year, now.month, now.day)
    weekday = WEEKDAYS[now.weekday()]
    return (
        f"{weekday} {to_persian_digits(jd)} "
        f"{JALALI_MONTHS[jm - 1]} {to_persian_digits(jy)}"
    )


# ============================================================
# پردازش فارسی
# ============================================================
def prepare_farsi_text(text: str) -> str:
    if not text:
        return ""
    return get_display(arabic_reshaper.reshape(text))


def draw_centered_text(draw, text, box, font, fill_color):
    if not text:
        return

    shaped = prepare_farsi_text(text)
    bbox = draw.textbbox((0, 0), shaped, font=font)
    width = bbox[2] - bbox[0]
    height = bbox[3] - bbox[1]

    x = box["x"] - width / 2
    y = box["y"] - height / 2
    draw.text((x, y), shaped, font=font, fill=fill_color)


def load_font(font_path: str, size: int):
    try:
        return ImageFont.truetype(font_path, size)
    except Exception:
        return ImageFont.load_default()


# ============================================================
# عکس — فقط تصویر ثابت، نه GIF و نه ویدیو
# ============================================================
def normalize_image_bytes(value) -> bytes:
    if value is None:
        raise ValueError("اطلاعات عکس خالی است.")

    if isinstance(value, bytes):
        raw = value
    elif isinstance(value, bytearray):
        raw = bytes(value)
    elif isinstance(value, memoryview):
        raw = value.tobytes()
    elif hasattr(value, "getvalue"):
        raw = value.getvalue()
    elif hasattr(value, "read"):
        try:
            old_pos = value.tell() if hasattr(value, "tell") else 0
            if hasattr(value, "seek"):
                value.seek(0)
            raw = value.read()
            if hasattr(value, "seek"):
                value.seek(old_pos)
        except Exception as exc:
            raise ValueError("خواندن دادهٔ عکس ممکن نشد.") from exc
    else:
        raise TypeError(f"نوع دادهٔ عکس پشتیبانی نمی‌شود: {type(value)!r}")

    if not isinstance(raw, bytes):
        raw = bytes(raw)

    if not raw:
        raise ValueError("فایل عکس خالی است.")

    try:
        with Image.open(io.BytesIO(raw)) as test_image:
            image_format = (test_image.format or "").upper()
            is_animated = bool(getattr(test_image, "is_animated", False))
            test_image.verify()

        if image_format not in ALLOWED_IMAGE_FORMATS:
            raise ValueError(
                "فرمت مجاز نیست. فقط JPG، JPEG، PNG و WEBP قابل انتخاب هستند."
            )

        if is_animated:
            raise ValueError("تصاویر متحرک مانند GIF مجاز نیستند.")

    except ValueError:
        raise
    except Exception as exc:
        raise ValueError(
            "فایل انتخاب‌شده یک تصویر معتبر نیست یا ناقص است."
        ) from exc

    return raw


# ============================================================
# ساخت پوستر
# ============================================================
def create_poster(template_path, font_path, output_path, data, photo_bytes=None):
    if not template_path.exists():
        raise FileNotFoundError(
            "فایل template.jpg پیدا نشد. آن را داخل پوشه assets قرار دهید."
        )

    if not font_path.exists():
        raise FileNotFoundError(
            "فونت calibrib.ttf پیدا نشد. آن را داخل پوشه assets قرار دهید."
        )

    img = Image.open(template_path).convert("RGBA")
    draw = ImageDraw.Draw(img)

    font_number = load_font(str(font_path), 43)
    font_title = load_font(str(font_path), 50)
    font_subject = load_font(str(font_path), 55)
    font_presenter = load_font(str(font_path), 26)
    font_date = load_font(str(font_path), 25)

    draw_centered_text(draw, data["number"], BOX_TOP_NUMBER, font_number, GOLD)
    draw_centered_text(draw, data["title"], BOX_TOP_TITLE, font_title, GOLD)

    lines = data["subject"].splitlines() or [""]
    line_spacing = 60
    total_height = len(lines) * line_spacing
    start_y = BOX_MIDDLE["y"] - total_height / 2 + 30

    for index, line in enumerate(lines):
        box = BOX_MIDDLE.copy()
        box["y"] = start_y + index * line_spacing
        draw_centered_text(draw, line, box, font_subject, NAVY)

    if photo_bytes:
        raw_photo = normalize_image_bytes(photo_bytes)
        try:
            with Image.open(io.BytesIO(raw_photo)) as source:
                photo = ImageOps.exif_transpose(source.convert("RGBA"))
                photo.load()

            target_w = BOX_PHOTO["w"]
            target_h = BOX_PHOTO["h"]
            photo.thumbnail((target_w, target_h), Image.Resampling.LANCZOS)

            canvas = Image.new("RGBA", (target_w, target_h), (0, 0, 0, 0))
            px = (target_w - photo.width) // 2
            py = (target_h - photo.height) // 2
            canvas.alpha_composite(photo, (px, py))

            paste_x = int(BOX_PHOTO["x"] - target_w / 2)
            paste_y = int(BOX_PHOTO["y"] - target_h / 2)
            img.alpha_composite(canvas, (paste_x, paste_y))
        except Exception as exc:
            raise RuntimeError(f"خطا در پردازش عکس ارائه‌دهنده: {exc}") from exc

    presenter_lines = data["presenter"].splitlines() or [""]
    presenter_spacing = 50
    presenter_total = len(presenter_lines) * presenter_spacing
    presenter_start_y = BOX_PRESENTER["y"] - presenter_total / 2 + 20

    for index, line in enumerate(presenter_lines):
        box = BOX_PRESENTER.copy()
        box["y"] = presenter_start_y + index * presenter_spacing
        draw_centered_text(draw, line, box, font_presenter, NAVY)

    draw_centered_text(draw, data["date"], BOX_DATE, font_date, NAVY)

    img.convert("RGB").save(output_path, "JPEG", quality=95)
    return output_path


def get_next_output_path(output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    highest = 0

    for name in os.listdir(output_dir):
        if not (name.startswith("poster_") and name.lower().endswith(".jpg")):
            continue
        try:
            number = int(name[7:-4])
            highest = max(highest, number)
        except ValueError:
            continue

    return output_dir / f"poster_{highest + 1}.jpg"


# ============================================================
# رابط کاربری
# ============================================================
def main(page: ft.Page):
    page.title = "پوستر ساز جلسات فقهی"
    page.theme_mode = ft.ThemeMode.DARK
    page.bgcolor = BG
    page.padding = 0
    page.scroll = ft.ScrollMode.AUTO

    def get_assets_dir() -> Path:
        default_assets_dir = Path(__file__).resolve().parent / "assets"
        return Path(
            os.environ.get("FLET_ASSETS_DIR", str(default_assets_dir))
        ).resolve()

    def get_output_dir() -> Path:
        storage_dir = os.environ.get("FLET_APP_STORAGE_DATA")
        if storage_dir:
            return Path(storage_dir).resolve() / "output"
        return Path(__file__).resolve().parent / "output"

    assets_dir = get_assets_dir()
    output_dir = get_output_dir()
    template_path = assets_dir / "template.jpg"
    font_path = assets_dir / "calibrib.ttf"
    output_dir.mkdir(parents=True, exist_ok=True)

    file_picker = ft.FilePicker()
    page.services.append(file_picker)
    share_service = ft.Share()

    selected_photo_bytes = {"value": None}
    current_poster = {"path": None, "bytes": None}

    def border_style():
        return {
            ft.ControlState.DEFAULT: ft.OutlineInputBorder(
                border_radius=10,
                side=ft.BorderSide(width=1, color=BORDER),
            ),
            ft.ControlState.FOCUSED: ft.OutlineInputBorder(
                border_radius=10,
                side=ft.BorderSide(width=2, color=GOLD),
            ),
        }

    # ---------------- فیلدها: عمداً خالی ----------------
    txt_number = ft.TextField(
        label="شماره جلسه",
        value="",
        text_align=ft.TextAlign.RIGHT,
        filled=True,
        bgcolor=PANEL_2,
        border=border_style(),
    )

    txt_title = ft.TextField(
        label="عنوان جلسه",
        value="",
        text_align=ft.TextAlign.RIGHT,
        filled=True,
        bgcolor=PANEL_2,
        border=border_style(),
    )

    txt_subject = ft.TextField(
        label="موضوع (چند خطی)",
        value="",
        multiline=True,
        min_lines=2,
        max_lines=4,
        text_align=ft.TextAlign.RIGHT,
        filled=True,
        bgcolor=PANEL_2,
        border=border_style(),
    )

    txt_presenter = ft.TextField(
        label="نام ارائه‌دهنده (چند خطی)",
        value="",
        multiline=True,
        min_lines=2,
        max_lines=3,
        text_align=ft.TextAlign.RIGHT,
        filled=True,
        bgcolor=PANEL_2,
        border=border_style(),
    )

    txt_date = ft.TextField(
        label="تاریخ برگزاری",
        value="",
        text_align=ft.TextAlign.RIGHT,
        filled=True,
        bgcolor=PANEL_2,
        border=border_style(),
    )

    txt_photo_status = ft.Text(
        "عکسی انتخاب نشده",
        color=MUTED,
        size=12,
    )

    status_text = ft.Text(
        "فرم آماده است",
        size=12,
        color=MUTED,
    )

    # ========================================================
    # پیش‌نمایش
    # ========================================================
    preview_image = ft.Image(
        src="",
        width=290,
        height=435,
        fit=ft.BoxFit.CONTAIN,
        visible=False,
    )

    preview_placeholder = ft.Container(
        width=290,
        height=435,
        bgcolor="#0C1F1A",
        border=ft.Border.all(1, "#2A433C"),
        border_radius=18,
        alignment=ft.Alignment.CENTER,
        content=ft.Column(
            [
                ft.Icon(ft.Icons.IMAGE_OUTLINED, size=48, color=MUTED),
                ft.Text("پیش‌نمایش پوستر", color=MUTED, size=15),
                ft.Text(
                    "پس از ساخت پوستر نمایش داده می‌شود",
                    color="#6E8179",
                    size=11,
                    text_align=ft.TextAlign.CENTER,
                ),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=8,
        ),
    )

    preview_stack = ft.Stack(
        [
            preview_placeholder,
            ft.Container(
                content=preview_image,
                alignment=ft.Alignment.CENTER,
            ),
        ],
        width=300,
        height=445,
    )

    # ========================================================
    # گالری
    # ========================================================
    saved_gallery = ft.GridView(
        expand=False,
        runs_count=2,
        max_extent=175,
        spacing=10,
        run_spacing=10,
        height=460,
    )

    gallery_title = ft.Column(
        [
            ft.Text(
                "پوسترهای ذخیره‌شده",
                size=20,
                weight=ft.FontWeight.BOLD,
                color=CREAM,
            ),
            ft.Text(
                "پوستر را ببینید یا حذف کنید",
                color=MUTED,
                size=11,
            ),
        ],
        spacing=2,
    )

    # ========================================================
    # توابع UI
    # ========================================================
    def show_message(message: str, error=False):
        status_text.value = message
        status_text.color = DANGER if error else MUTED
        page.show_dialog(
            ft.SnackBar(content=ft.Text(message, color=ft.Colors.BLACK))
        )
        page.update()

    def read_poster_bytes(path: Path) -> bytes:
        with open(path, "rb") as f:
            return f.read()

    def clear_preview():
        preview_image.visible = False
        preview_image.src = ""
        preview_placeholder.visible = True
        current_poster["path"] = None
        current_poster["bytes"] = None

    def set_preview(path: Path):
        try:
            image_bytes = read_poster_bytes(path)
        except (OSError, IOError) as exc:
            show_message(f"خطا در خواندن پوستر: {exc}", error=True)
            return

        preview_image.src = image_bytes
        preview_image.visible = True
        preview_placeholder.visible = False
        current_poster["path"] = path
        current_poster["bytes"] = image_bytes
        page.update()

    def saved_posters():
        if not output_dir.exists():
            return []
        files = [
            path
            for path in output_dir.iterdir()
            if path.is_file()
               and path.name.startswith("poster_")
               and path.suffix.lower() == ".jpg"
        ]
        return sorted(files, key=lambda p: p.stat().st_mtime, reverse=True)

    def delete_poster(path: Path):
        try:
            if not path.exists():
                show_message("این پوستر قبلاً حذف شده است.", error=True)
                return

            path.unlink()

            if current_poster["path"] == path:
                clear_preview()

            refresh_gallery()
            show_message(f"پوستر {path.name} حذف شد.")
        except Exception as exc:
            show_message(f"حذف پوستر انجام نشد: {exc}", error=True)

    def refresh_gallery():
        saved_gallery.controls.clear()
        files = saved_posters()

        if not files:
            saved_gallery.controls.append(
                ft.Container(
                    content=ft.Text(
                        "هنوز پوستری ذخیره نشده است.",
                        color=MUTED,
                        size=12,
                        text_align=ft.TextAlign.CENTER,
                    ),
                    alignment=ft.Alignment.CENTER,
                    padding=20,
                )
            )
            page.update()
            return

        for path in files:
            try:
                thumbnail_bytes = read_poster_bytes(path)
            except (OSError, IOError):
                continue

            def open_saved(e, selected_path=path):
                set_preview(selected_path)
                status_text.value = f"نمایش {selected_path.name}"
                page.update()

            def remove_saved(e, selected_path=path):
                delete_poster(selected_path)

            card = ft.Container(
                width=160,
                padding=7,
                bgcolor=PANEL,
                border=ft.Border.all(1, BORDER),
                border_radius=12,
                content=ft.Column(
                    [
                        ft.Image(
                            src=thumbnail_bytes,
                            width=140,
                            height=210,
                            fit=ft.BoxFit.CONTAIN,
                            border_radius=8,
                        ),
                        ft.Text(
                            path.name,
                            size=10,
                            color=MUTED,
                            text_align=ft.TextAlign.CENTER,
                        ),
                        ft.Button(
                            content="حذف پوستر",
                            icon=ft.Icons.DELETE_OUTLINE,
                            on_click=remove_saved,
                            style=ft.ButtonStyle(
                                color=DANGER,
                            ),
                        ),
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=5,
                ),
                on_click=open_saved,
            )
            saved_gallery.controls.append(card)

        page.update()

    # ========================================================
    # انتخاب عکس
    # ========================================================
    def handle_photo_result(e: ft.FilePickerResultEvent):
        if not e.files:
            return

        selected = e.files[0]
        selected_photo_bytes["value"] = None

        try:
            if selected.bytes:
                selected_photo_bytes["value"] = normalize_image_bytes(selected.bytes)
        except Exception:
            selected_photo_bytes["value"] = None

        if not selected_photo_bytes["value"] and getattr(selected, "path", None):
            try:
                with open(selected.path, "rb") as f:
                    selected_photo_bytes["value"] = normalize_image_bytes(f.read())
            except Exception:
                selected_photo_bytes["value"] = None

        if not selected_photo_bytes["value"]:
            show_message(
                "فقط عکس ثابت JPG، PNG یا WEBP قابل استفاده است؛ GIF و ویدیو مجاز نیست.",
                error=True,
            )
            return

        txt_photo_status.value = f"انتخاب شد: {selected.name}"
        txt_photo_status.color = SUCCESS
        status_text.value = "عکس آماده ساخت پوستر است"
        status_text.color = MUTED
        page.update()

    file_picker.on_result = handle_photo_result

    btn_select_photo = ft.Button(
        content="انتخاب عکس از گالری",
        icon=ft.Icons.IMAGE_OUTLINED,
        action=ft.PickFiles(
            file_picker,
            allow_multiple=False,
            file_type=ft.FilePickerFileType.IMAGE,
            with_data=True,
        ),
    )

    # ========================================================
    # تاریخ امروز
    # ========================================================
    def set_today(e):
        txt_date.value = today_jalali_text()
        status_text.value = "تاریخ امروز وارد شد"
        status_text.color = MUTED
        page.update()

    btn_today = ft.Button(
        content="تاریخ امروز",
        icon=ft.Icons.TODAY,
        on_click=set_today,
    )

    # ========================================================
    # پاک کردن فرم
    # ========================================================
    def clear_form(e):
        txt_number.value = ""
        txt_title.value = ""
        txt_subject.value = ""
        txt_presenter.value = ""
        txt_date.value = ""
        selected_photo_bytes["value"] = None
        txt_photo_status.value = "عکسی انتخاب نشده"
        txt_photo_status.color = MUTED
        status_text.value = "فرم خالی شد"
        status_text.color = MUTED
        clear_preview()
        page.update()

    btn_clear = ft.Button(
        content="پاک کردن فرم",
        icon=ft.Icons.CLEAR_ALL,
        on_click=clear_form,
    )

    # ========================================================
    # ساخت پوستر
    # ========================================================
    async def generate_and_save(e):
        if not txt_number.value and not txt_title.value and not txt_subject.value and not txt_presenter.value and not txt_date.value:
            show_message("ابتدا اطلاعات جلسه را وارد کنید.", error=True)
            return

        if not selected_photo_bytes["value"]:
            show_message("ابتدا یک عکس معتبر از گالری انتخاب کنید.", error=True)
            return

        data = {
            "number": txt_number.value or "",
            "title": txt_title.value or "",
            "subject": txt_subject.value or "",
            "presenter": txt_presenter.value or "",
            "date": txt_date.value or "",
        }

        output_path = get_next_output_path(output_dir)

        try:
            create_poster(
                template_path,
                font_path,
                output_path,
                data,
                selected_photo_bytes["value"],
            )

            poster_bytes = read_poster_bytes(output_path)
            current_poster["path"] = output_path
            current_poster["bytes"] = poster_bytes

            set_preview(output_path)
            refresh_gallery()
            show_message(f"پوستر ساخته و ذخیره شد: {output_path.name}")

        except Exception as exc:
            try:
                if output_path.exists():
                    output_path.unlink()
            except Exception:
                pass
            show_message(f"خطا در ساخت پوستر: {exc}", error=True)

    btn_generate = ft.Button(
        content="ساخت و ذخیره پوستر",
        icon=ft.Icons.SAVE,
        on_click=generate_and_save,
        style=ft.ButtonStyle(
            bgcolor=GOLD,
            color=BG,
        ),
    )

    # ========================================================
    # ذخیره / دانلود
    # ========================================================
    async def save_current(e):
        data = current_poster["bytes"]
        if not data:
            show_message("ابتدا یک پوستر بسازید یا از گالری انتخاب کنید.", error=True)
            return

        try:
            path = await file_picker.save_file(
                dialog_title="ذخیره پوستر",
                file_name="poster.jpg",
                file_type=ft.FilePickerFileType.CUSTOM,
                allowed_extensions=["jpg"],
                src_bytes=data,
            )
            if page.web:
                show_message("دانلود پوستر آغاز شد.")
            elif path:
                show_message(f"پوستر ذخیره شد:\n{path}")
            else:
                show_message("عملیات ذخیره لغو شد.")
        except Exception as exc:
            show_message(f"خطا در ذخیره پوستر: {exc}", error=True)

    btn_save_as = ft.Button(
        content="ذخیره / دانلود",
        icon=ft.Icons.DOWNLOAD,
        on_click=save_current,
    )

    # ========================================================
    # داده‌های متون واردشده توسط کاربر
    # این تابع عمداً قبل از share_current تعریف شده است.
    # ========================================================
    def get_session_data():
        return {
            "number": txt_number.value or "",
            "title": txt_title.value or "",
            "subject": txt_subject.value or "",
            "presenter": txt_presenter.value or "",
            "date": txt_date.value or "",
        }

    # ========================================================
    # اشتراک‌گذاری
    # ========================================================
    async def share_current(e):
        data = current_poster["bytes"]
        if not data:
            show_message("ابتدا یک پوستر بسازید.", error=True)
            return

        try:
            if page.web:
                await file_picker.save_file(
                    dialog_title="دانلود پوستر",
                    file_name="poster.jpg",
                    file_type=ft.FilePickerFileType.CUSTOM,
                    allowed_extensions=["jpg"],
                    src_bytes=data,
                )
                show_message("در نسخه وب، پوستر برای دانلود آماده شد.")
                return

            share_file = ft.ShareFile.from_bytes(
                data,
                mime_type="image/jpeg",
                name="poster.jpg",
            )
            session_data = get_session_data()
            text_message = f'''{session_data['number'] + session_data['title']}

با موضوع 
{session_data['subject']}

در محضر 
{session_data["presenter"]}

{session_data['date']}

https://eitaa.com/shfeghhi
https://t.me/shfeghhi'''

            result = await share_service.share_files(
                [share_file],
                title="اشتراک‌گذاری پوستر",
                text=text_message,
            )
            show_message(f"وضعیت اشتراک‌گذاری: {result.status}")
        except Exception as exc:
            show_message(f"خطا در اشتراک‌گذاری: {exc}", error=True)

    btn_share = ft.Button(
        content="اشتراک‌گذاری",
        icon=ft.Icons.SHARE,
        on_click=share_current,
    )

    preview_actions = ft.Column(
        [btn_save_as, btn_share],
        horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
        spacing=8,
    )

    # ========================================================
    # پنل فرم
    # ========================================================
    form_panel = ft.Container(
        expand=True,
        padding=14,
        bgcolor=PANEL,
        border_radius=20,
        content=ft.Column(
            [
                ft.Text(
                    "مشخصات جلسه",
                    size=20,
                    weight=ft.FontWeight.BOLD,
                    color=CREAM,
                ),
                txt_number,
                txt_title,
                txt_subject,
                txt_presenter,
                txt_date,
                ft.Row(
                    [btn_today, btn_clear],
                    spacing=8,
                ),
                ft.Container(
                    padding=10,
                    bgcolor=PANEL_2,
                    border_radius=12,
                    content=ft.Column(
                        [
                            ft.Text(
                                "عکس ارائه‌دهنده",
                                size=12,
                                color=CREAM,
                            ),
                            btn_select_photo,
                            txt_photo_status,
                        ],
                        spacing=8,
                    ),
                ),
                btn_generate,
                status_text,
            ],
            spacing=10,
        ),
    )

    # ========================================================
    # پنل پیش‌نمایش
    # ========================================================
    preview_panel = ft.Container(
        expand=True,
        padding=12,
        bgcolor=PANEL,
        border_radius=20,
        content=ft.Column(
            [
                ft.Text(
                    "پیش‌نمایش",
                    size=20,
                    weight=ft.FontWeight.BOLD,
                    color=CREAM,
                ),
                ft.Row(
                    [preview_stack],
                    alignment=ft.MainAxisAlignment.CENTER,
                ),
                preview_actions,
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=10,
        ),
    )

    # ========================================================
    # سربرگ
    # ========================================================
    header = ft.Container(
        padding=ft.Padding.symmetric(horizontal=12, vertical=12),
        border=ft.Border.only(
            bottom=ft.BorderSide(width=1, color="#1C3430")
        ),
        content=ft.Column(
            [
                ft.Text(
                    "پوستر ساز جلسات فقهی",
                    size=21,
                    weight=ft.FontWeight.BOLD,
                    color=CREAM,
                    text_align=ft.TextAlign.RIGHT,
                ),
                ft.Text(
                    "ساخت پوستر، پیش‌نمایش، ذخیره، حذف و اشتراک‌گذاری",
                    size=11,
                    color=MUTED,
                    text_align=ft.TextAlign.RIGHT,
                ),
            ],
            spacing=2,
        ),
    )

    # ========================================================
    # صفحه موبایل
    # ========================================================
    page.add(
        ft.Column(
            [
                header,
                ft.Container(
                    padding=ft.Padding.symmetric(horizontal=10, vertical=12),
                    content=ft.Column(
                        [
                            preview_panel,
                            form_panel,
                            ft.Divider(color="#1C3430", height=18),
                            gallery_title,
                            saved_gallery,
                        ],
                        spacing=12,
                    ),
                ),
            ],
            spacing=0,
        )
    )

    refresh_gallery()

if __name__ == "__main__":
    ft.run(main, assets_dir="assets")