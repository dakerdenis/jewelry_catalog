# catalog/admin.py
from django.contrib import admin
from django.utils.html import format_html
from django.forms.models import BaseInlineFormSet

from django import forms  # <-- добавь импорт
from .models import (
    Collection, Category, Product, ProductImage,
    LandingConfig, LandingThreeItem
)
@admin.register(Collection)
class CollectionAdmin(admin.ModelAdmin):
    list_display = ("name", "quick_link")
    search_fields = ("name", "description")
    prepopulated_fields = {"slug": ("name",)}



@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name",)
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
    def thumbnail(self, obj):
        first = obj.images.first()
        if first and first.image:
            try:
                return format_html('<img src="{}" style="height:60px; border-radius:6px;" />', first.image.url)
            except Exception:
                return "—"
        return "—"
    thumbnail.short_description = "Photo"

# ProductAdmin
    list_display = ("thumbnail", "name", "collection", "category", "price", "currency", "material", "is_active", "stock")
    list_filter  = ("collection", "category", "material", "metal_color", "is_active")
    search_fields = ("name", "description", "sku", "gemstone")
    prepopulated_fields = {"slug": ("name",)}
    inlines = [ProductImageInline]
    readonly_fields = ("gallery",)

    fieldsets = (
        (None, {"fields": ("collection", "category", "name", "slug", "description")}),
        ("Commerce", {"fields": ("price", "currency", "sku", "stock", "is_active")}),
        ("Jewelry", {"fields": ("material", "metal_color", "metal_purity_karat", "weight_grams",
                                "gemstone", "gemstone_carat", "ring_size")}),
        ("Images preview", {"fields": ("gallery",)}),
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



class LimitThreeInlineFormset(BaseInlineFormSet):
    def clean(self):
        super().clean()
        active_forms = [
            f for f in self.forms
            if getattr(f, "cleaned_data", None)
            and not f.cleaned_data.get("DELETE", False)
        ]
        count = len(active_forms)
        if count < 1:
            raise forms.ValidationError("Select at least 1 product for the 3-items block.")
        if count > 3:
            raise forms.ValidationError("Select no more than 3 products for the 3-items block.")

        positions = set()
        products = set()
        for f in active_forms:
            pos = f.cleaned_data.get("position")
            prod = f.cleaned_data.get("product")
            if pos in positions:
                raise forms.ValidationError("Positions must be unique (1, 2, 3).")
            if prod in products:
                raise forms.ValidationError("Products must be unique.")
            positions.add(pos)
            products.add(prod)


class LandingThreeItemInline(admin.TabularInline):
    model = LandingThreeItem
    extra = 3
    min_num = 1
    max_num = 3
    formset = LimitThreeInlineFormset
    autocomplete_fields = ("product",)
    fields = ("position", "product", "preview")
    readonly_fields = ("preview",)

    def preview(self, obj):
        if obj and getattr(obj, "product", None):
            first = obj.product.images.first()
            if first and first.image:
                try:
                    return format_html('<img src="{}" style="height:60px;border-radius:6px;" />', first.image.url)
                except Exception:
                    pass
        return "—"
    preview.short_description = "Preview"


@admin.register(LandingConfig)
class LandingConfigAdmin(admin.ModelAdmin):
    form = LandingConfigAdminForm
    filter_horizontal = ("goods",)  # твой блок с «до 2 товаров» для другой секции
    list_display = ("__str__", "get_goods_count", "get_three_count")
    inlines = [LandingThreeItemInline]

    def get_goods_count(self, obj):
        return obj.goods.count()
    get_goods_count.short_description = "Selected (2-items)"

    def get_three_count(self, obj):
        return obj.three_products.count()
    get_three_count.short_description = "Selected (3-items)"