from django.shortcuts import render, get_object_or_404
from .models import Collection, Product

def landing_view(request):
    # TODO: в будущем сюда подтянем «избранные» коллекции/фото
    return render(request, "catalog/landing.html", {})

def product_list_view(request):
    # TODO: позже добавим фильтры, пагинацию, сортировку
    return render(request, "catalog/product_list.html", {})

def product_detail_view(request, slug: str):
    # TODO: позже полноценные данные, похожие товары, галерея
    # Заглушка: попытаемся найти продукт по slug, иначе 404 (это уже полезно)
    product = get_object_or_404(Product.objects.only("id", "name", "slug"), slug=slug)
    return render(request, "catalog/product_detail.html", {"product": product})
