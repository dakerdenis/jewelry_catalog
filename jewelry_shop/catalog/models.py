# catalog/models.py
from decimal import Decimal
from io import BytesIO
from pathlib import Path

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.urls import reverse
from django.utils.text import slugify
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
    Создаёт для файла из ImageField варианты шириной 350/525 в JPG (q=80) и WebP (q=75).
    """
    if not image_field or not image_field.name:
        return
    with default_storage.open(image_field.name, "rb") as f:
        im = Image.open(f)
        im.load()

    src_path = Path(image_field.name)
    stem = src_path.stem
    parent = src_path.parent.as_posix()

    for w in TARGET_WIDTHS:
        h = round(im.height * (w / im.width))
        resized = im.copy().resize((w, h), Image.LANCZOS)

        jpg_name  = f"{parent}/{stem}-{w}w.jpg"
        webp_name = f"{parent}/{stem}-{w}w.webp"

        if not default_storage.exists(jpg_name):
            _save_variant(resized, jpg_name, "jpg", quality=80)
        if not default_storage.exists(webp_name):
            _save_variant(resized, webp_name, "webp", quality=75)

class TimestampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Collection(TimestampedModel):
    name = models.CharField(max_length=200, unique=True)
    slug = models.SlugField(max_length=220, unique=True, help_text="Auto-filled from name")
    description = models.TextField(blank=True)
    photo = models.ImageField(upload_to="collections/%Y/%m/%d/", blank=True, null=True)
    quick_link = models.URLField(
        blank=True,
        help_text="External quick link (e.g., landing or promo URL)"
    )

    class Meta:
        ordering = ["name"]
        indexes = [models.Index(fields=["slug"])]

    def __str__(self) -> str:
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
    def get_absolute_url(self):
        # когда появится страница коллекции — поменяем маршрут
        return reverse("catalog:landing")


# --- Category: глобальная, без связи с Collection ---
class Category(TimestampedModel):
    name = models.CharField(max_length=200, unique=True)
    slug = models.SlugField(max_length=220, unique=True, help_text="Auto-filled from name")
    description = models.TextField(blank=True)

    class Meta:
        ordering = ["name"]
        indexes = [models.Index(fields=["slug"])]

    def __str__(self) -> str:
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("catalog:list")


class MaterialType(models.TextChoices):
    GOLD = "gold", "Gold"
    SILVER = "silver", "Silver"
    PLATINUM = "platinum", "Platinum"
    OTHER = "other", "Other"


class MetalColor(models.TextChoices):
    YELLOW = "yellow", "Yellow"
    WHITE = "white", "White"
    ROSE = "rose", "Rose"
    MIXED = "mixed", "Mixed"
    NONE = "none", "None"


# --- Product: теперь хранит и collection, и category ---
class Product(TimestampedModel):
    collection = models.ForeignKey(  # NEW
        Collection,
        on_delete=models.PROTECT,
        related_name="products",
    )
    category = models.ForeignKey(    # как и было, но теперь к глобальной Category
        Category,
        on_delete=models.PROTECT,
        related_name="products",
    )

    name = models.CharField(max_length=250)
    slug = models.SlugField(max_length=270, unique=True, help_text="Auto-filled from name")
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=12, decimal_places=2,
                                validators=[MinValueValidator(Decimal("0.0"))])
    currency = models.CharField(max_length=3, default="USD")
    sku = models.CharField(max_length=64, unique=True, help_text="Stock keeping unit / article code")

    material = models.CharField(max_length=20, choices=MaterialType.choices, default=MaterialType.GOLD)
    metal_color = models.CharField(max_length=10, choices=MetalColor.choices, default=MetalColor.NONE)
    metal_purity_karat = models.PositiveSmallIntegerField(blank=True, null=True, help_text="e.g., 14, 18")
    weight_grams = models.DecimalField(max_digits=7, decimal_places=2, blank=True, null=True)
    gemstone = models.CharField(max_length=120, blank=True, help_text="e.g., Diamond, Emerald")
    gemstone_carat = models.DecimalField(max_digits=6, decimal_places=3, blank=True, null=True)
    ring_size = models.CharField(max_length=16, blank=True)

    stock = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]
        indexes = [
            models.Index(fields=["slug"]),
            models.Index(fields=["collection"]),
            models.Index(fields=["category"]),
            models.Index(fields=["is_active"]),
        ]

    def __str__(self) -> str:
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("catalog:detail", kwargs={"slug": self.slug})


def product_image_upload_to(instance: "ProductImage", filename: str) -> str:
    return f"products/{instance.product.id or 'new'}/{filename}"


class ProductImage(TimestampedModel):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="images")
    image = models.ImageField(upload_to=product_image_upload_to)
    alt_text = models.CharField(max_length=200, blank=True)

    class Meta:
        ordering = ["id"]

    # ---- ссылки на варианты ----
    def _variant_name(self, w: int, ext: str) -> str:
        p = Path(self.image.name)
        return str(p.with_name(f"{p.stem}-{w}w.{ext}"))

    def _variant_url(self, w: int, ext: str):
        name = self._variant_name(w, ext)
        if default_storage.exists(name):
            return settings.MEDIA_URL + name
        return None

    @property
    def url_350_webp(self): return self._variant_url(350, "webp")
    @property
    def url_350_jpg(self):  return self._variant_url(350, "jpg")
    @property
    def url_525_webp(self): return self._variant_url(525, "webp")
    @property
    def url_525_jpg(self):  return self._variant_url(525, "jpg")

@receiver(post_save, sender=ProductImage)
def build_variants_on_save(sender, instance: "ProductImage", **kwargs):
    try:
        generate_variants(instance.image)
    except Exception:
        # не валим запрос, если Pillow не смог — просто пропустим
        pass




class LandingConfig(TimestampedModel):
    goods = models.ManyToManyField(
        Product,
        blank=True,
        related_name="featured_on_landing",
        help_text="Pick up to 2 products to display on the landing page."
    )

    class Meta:
        verbose_name = "Landing configuration"
        verbose_name_plural = "Landing configuration"  # будет один список в админке

    def __str__(self) -> str:
        return "Landing configuration"




class LandingThreeItem(TimestampedModel):
    """
    Один элемент секции '3 товара' на главной.
    Выбранный продукт + его позиция (1..3) внутри секции.
    """
    config = models.ForeignKey(
        LandingConfig,
        on_delete=models.CASCADE,
        related_name="three_products",
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT,
        limit_choices_to={"is_active": True},
        related_name="featured_in_three",
    )
    position = models.PositiveSmallIntegerField(
        choices=[(1, "1"), (2, "2"), (3, "3")],
        help_text="Position in the 3-items block (1..3)",
    )

    class Meta:
        unique_together = (
            ("config", "position"),  # позиция уникальна
            ("config", "product"),   # продукт не повторяется
        )
        ordering = ["position"]

    def __str__(self):
        return f"#{self.position}: {self.product.name}"
