# catalog/models.py
from django.db import models
from django.utils.text import slugify
from django.core.validators import MinValueValidator
from decimal import Decimal
from django.urls import reverse
from django.core.exceptions import ValidationError

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