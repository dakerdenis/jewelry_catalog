# catalog/views.py
from django.shortcuts import render, get_object_or_404
from django.db.models import Prefetch
from .models import Collection, Product, ProductImage, LandingConfig

def landing_view(request):
    cfg = (
        LandingConfig.objects
        .prefetch_related("goods__images")  # чтобы не было N+1 для картинок
        .first()
    )
    landing_goods = []
    if cfg:
        landing_goods = (
            cfg.goods
            .filter(is_active=True)
            .prefetch_related("images")
        )[:2]  # страховка: не больше двух
    return render(request, "catalog/landing.html", {"landing_goods": landing_goods})


def product_list_view(request):
    # Все активные товары + категории + фотки (для превью)
    products = (
        Product.objects.filter(is_active=True)
        .select_related("category", "category__collection")
        .prefetch_related("images")   # хватит для первой фотки
        .order_by("name")
    )
    return render(request, "catalog/product_list.html", {"products": products})

def product_detail_view(request, slug: str):
    product = get_object_or_404(Product.objects.only("id", "name", "slug"), slug=slug)
    return render(request, "catalog/product_detail.html", {"product": product})
