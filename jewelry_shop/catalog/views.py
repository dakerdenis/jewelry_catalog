# catalog/views.py
from django.shortcuts import render, get_object_or_404
from django.db.models import Prefetch
from .models import Collection, Product, ProductImage, LandingConfig
from .models import LandingThreeItem

def landing_view(request):
    cfg = (
        LandingConfig.objects
        .prefetch_related(
            "goods__images",  # для секции из 2 товаров (что делали раньше)
            Prefetch(
                "three_products",
                queryset=(
                    # подтянем product + его изображения
                    # ordering у модели уже по position
                    # но на всякий укажем ещё раз
                    LandingThreeItem.objects
                    .select_related("product")
                    .order_by("position")
                ),
                to_attr="prefetched_three"  # сохраним в атрибут
            ),
        )
        .first()
    )

    landing_goods = []  # 0..2 — старая секция, если используешь
    landing_three = []  # 1..3 — новая секция

    if cfg:
        # старая секция (можно оставить как было)
        landing_goods = (
            cfg.goods.filter(is_active=True)
            .prefetch_related("images")
        )[:2]

        # новая секция 1..3 с порядком
        if hasattr(cfg, "prefetched_three"):
            # из инлайна получаем продукты по порядку
            products = [
                item.product for item in cfg.prefetched_three
                if item.product and item.product.is_active
            ]
            # подгружаем изображения для списка продуктов
            landing_three = (
                Product.objects
                .filter(id__in=[p.id for p in products])
                .prefetch_related("images")
            )
            # сохраним порядок 1..3
            by_id = {p.id: p for p in landing_three}
            landing_three = [by_id[p.id] for p in products if p.id in by_id]

    return render(request, "catalog/landing.html", {
        "landing_goods": landing_goods,
        "landing_three": landing_three,
    })
    
    
    
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
