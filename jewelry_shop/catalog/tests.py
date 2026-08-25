from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from catalog.models import Category, Collection, Product


class ModelTest(TestCase):
    """Model creation, slug auto-fill, and string representation."""

    def setUp(self):
        self.collection = Collection.objects.create(name="Rings")
        self.category = Category.objects.create(name="Wedding")

    def test_collection_str_and_autoslug(self):
        self.assertEqual(str(self.collection), "Rings")
        # slug is auto-filled from name on save
        self.assertEqual(self.collection.slug, "rings")

    def test_category_str_and_autoslug(self):
        self.assertEqual(str(self.category), "Wedding")
        self.assertEqual(self.category.slug, "wedding")

    def test_product_creation_and_str(self):
        product = Product.objects.create(
            collection=self.collection,
            category=self.category,
            name="Gold Diamond Ring",
            price=Decimal("1200.00"),
            sku="RING-001",
        )
        self.assertEqual(str(product), "Gold Diamond Ring")
        self.assertEqual(product.slug, "gold-diamond-ring")

    def test_product_absolute_url_uses_slug(self):
        product = Product.objects.create(
            collection=self.collection,
            category=self.category,
            name="Silver Band",
            price=Decimal("300.00"),
            sku="RING-002",
        )
        self.assertEqual(product.get_absolute_url(), f"/product/{product.slug}/")

    def test_default_material_is_gold(self):
        product = Product.objects.create(
            collection=self.collection,
            category=self.category,
            name="Test Item",
            price=Decimal("50.00"),
            sku="SKU-003",
        )
        self.assertEqual(product.material, "gold")


class ViewTest(TestCase):
    """Public page responses and routing."""

    def setUp(self):
        collection = Collection.objects.create(name="Necklaces")
        category = Category.objects.create(name="Classic")
        self.product = Product.objects.create(
            collection=collection,
            category=category,
            name="Pearl Necklace",
            price=Decimal("800.00"),
            sku="NECK-001",
        )

    def test_landing_page_returns_200(self):
        response = self.client.get(reverse("catalog:landing"))
        self.assertEqual(response.status_code, 200)

    def test_catalog_list_returns_200(self):
        response = self.client.get(reverse("catalog:list"))
        self.assertEqual(response.status_code, 200)

    def test_collections_page_returns_200(self):
        response = self.client.get(reverse("catalog:collections"))
        self.assertEqual(response.status_code, 200)

    def test_product_detail_returns_200(self):
        response = self.client.get(
            reverse("catalog:detail", kwargs={"slug": self.product.slug})
        )
        self.assertEqual(response.status_code, 200)

    def test_unknown_product_returns_404(self):
        response = self.client.get(
            reverse("catalog:detail", kwargs={"slug": "does-not-exist"})
        )
        self.assertEqual(response.status_code, 404)
