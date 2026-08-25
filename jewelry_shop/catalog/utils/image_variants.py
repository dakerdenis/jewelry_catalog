# -*- coding: utf-8 -*-
from io import BytesIO
from pathlib import Path

from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from PIL import Image

TARGET_WIDTHS = (350, 525)

def _save_variant(pil_img, name, fmt, **save_kwargs):
    buf = BytesIO()
    if fmt.lower() == "jpg":
        pil_img = pil_img.convert("RGB")
        pil_img.save(buf, "JPEG", optimize=True, **save_kwargs)
    elif fmt.lower() == "webp":
        pil_img.save(buf, "WEBP", method=6, **save_kwargs)
    else:
        raise ValueError("Unsupported format")
    buf.seek(0)
    default_storage.save(name, ContentFile(buf.read()))

def generate_variants(image_field):
    """
    image_field: models.ImageField (например ProductImage.image)
    Создаёт варианты шириной 350/525 в JPG и WebP.
    """
    if not image_field or not image_field.name:
        return

    src_name = image_field.name
    with default_storage.open(src_name, "rb") as f:
        im = Image.open(f)
        im.load()

    src_path = Path(src_name)
    stem = src_path.stem
    parent = src_path.parent.as_posix()

    for w in TARGET_WIDTHS:
        # вычислим высоту по пропорции
        h = round(im.height * (w / im.width))
        resized = im.copy()
        resized = resized.resize((w, h), Image.LANCZOS)

        jpg_name  = f"{parent}/{stem}-{w}w.jpg"
        webp_name = f"{parent}/{stem}-{w}w.webp"

        # если нет — сохраняем
        if not default_storage.exists(jpg_name):
            _save_variant(resized, jpg_name, "jpg", quality=80)
        if not default_storage.exists(webp_name):
            _save_variant(resized, webp_name, "webp", quality=75)
