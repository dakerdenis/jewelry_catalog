# catalog/views.py
from django.shortcuts import render, get_object_or_404
from django.db.models import Prefetch, Count, Q
from .models import Collection, Category, Product, ProductImage, LandingConfig, LandingThreeItem

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
    selected_collections = request.GET.getlist("collection")
    selected_categories  = request.GET.getlist("category")

    products_qs = (
        Product.objects.filter(is_active=True)
        .select_related("collection", "category")
        .prefetch_related("images")
        .order_by("name")
    )
    if selected_collections:
        products_qs = products_qs.filter(collection__slug__in=selected_collections)
    if selected_categories:
        products_qs = products_qs.filter(category__slug__in=selected_categories)

    total_results = products_qs.count()

    # фасет «Коллекции» — учитывает выбранные категории
    collections = (
        Collection.objects
        .annotate(
            product_count=Count(
                "products",
                filter=Q(products__is_active=True) &
                       (Q(products__category__slug__in=selected_categories) if selected_categories else Q()),
                distinct=True,
            )
        )
        .order_by("name")
    )

    # фасет «Категории» (глобальные) — учитывает выбранные коллекции
    categories = (
        Category.objects
        .annotate(
            product_count=Count(
                "products",
                filter=Q(products__is_active=True) &
                       (Q(products__collection__slug__in=selected_collections) if selected_collections else Q()),
                distinct=True,
            )
        )
        .order_by("name")
    )

    context = {
        "products": products_qs,
        "collections": collections,
        "categories": categories,
        "selected_collections": selected_collections,
        "selected_categories": selected_categories,
        "total_results": total_results,
    }
    return render(request, "catalog/product_list.html", context)










def product_detail_view(request, slug: str):
    product = get_object_or_404(Product.objects.only("id", "name", "slug"), slug=slug)
    return render(request, "catalog/product_detail.html", {"product": product})


# catalog/views.py
def collections_view(request):
    collections = (
        Collection.objects.only("id", "name", "slug", "description", "photo", "quick_link")
        .annotate(product_count=Count("products", filter=Q(products__is_active=True), distinct=True))
        .order_by("name")
    )
    return render(request, "catalog/collections.html", {"collections": collections})










