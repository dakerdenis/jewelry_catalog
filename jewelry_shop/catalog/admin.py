# catalog/admin.py
from django.contrib import admin
from django.utils.html import format_html

from django import forms  # <-- добавь импорт
from .models import Collection, Category, Product, ProductImage, LandingConfig 

@admin.register(Collection)
class CollectionAdmin(admin.ModelAdmin):
    list_display = ("name", "quick_link")
    search_fields = ("name", "description")
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "collection")
    list_filter = ("collection",)
    search_fields = ("name", "description")
    prepopulated_fields = {"slug": ("name",)}


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1
    max_num = 5
    min_num = 0

    # показываем превью каждой строки инлайна
    fields = ("image", "alt_text", "preview")
    readonly_fields = ("preview",)

    def preview(self, obj):
        if obj and getattr(obj, "image", None):
            try:
                return format_html(
                    '<img src="{}" style="height:80px; border-radius:6px;" />',
                    obj.image.url,
                )
            except Exception:
                return "—"
        return "—"

    preview.short_description = "Preview"


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    # мини-превью первой фотки в списке товаров
    def thumbnail(self, obj):
        first = obj.images.first()
        if first and first.image:
            try:
                return format_html(
                    '<img src="{}" style="height:60px; border-radius:6px;" />',
                    first.image.url,
                )
            except Exception:
                return "—"
        return "—"
    thumbnail.short_description = "Photo"

    list_display = ("thumbnail", "name", "category", "price", "currency", "material", "is_active", "stock")
    list_filter = ("category__collection", "category", "material", "is_active", "metal_color")
    search_fields = ("name", "description", "sku", "gemstone")
    prepopulated_fields = {"slug": ("name",)}
    inlines = [ProductImageInline]

    # галерея-превью на странице редактирования товара
    readonly_fields = ("gallery",)

    fieldsets = (
        (None, {
            "fields": ("category", "name", "slug", "description")
        }),
        ("Commerce", {
            "fields": ("price", "currency", "sku", "stock", "is_active")
        }),
        ("Jewelry", {
            "fields": ("material", "metal_color", "metal_purity_karat", "weight_grams", "gemstone", "gemstone_carat", "ring_size")
        }),
        ("Images preview", {
            "fields": ("gallery",),
        }),
    )

    def gallery(self, obj):
        # при создании нового товара (obj None) просто ничего не рисуем
        if not obj or not obj.pk:
            return "—"
        imgs = obj.images.all()
        if not imgs:
            return "—"
        # простая галерея из всех фото
        thumbs = "".join(
            f'<img src="{i.image.url}" style="height:90px; margin:4px; border-radius:8px;" />'
            for i in imgs if i.image
        )
        return format_html(thumbs)
    gallery.short_description = "Current photos"

    # маленькая оптимизация списка
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.prefetch_related("images")

class LandingConfigAdminForm(forms.ModelForm):
    class Meta:
        model = LandingConfig
        fields = ["goods"]

    def clean_goods(self):
        goods = self.cleaned_data.get("goods")
        if goods and goods.count() > 2:
            raise forms.ValidationError("You can select at most 2 products.")
        return goods


@admin.register(LandingConfig)
class LandingConfigAdmin(admin.ModelAdmin):
    form = LandingConfigAdminForm
    filter_horizontal = ("goods",)  # удобный виджет выбора
    list_display = ("__str__", "get_goods_count")

    def get_goods_count(self, obj):
        return obj.goods.count()
    get_goods_count.short_description = "Selected products"