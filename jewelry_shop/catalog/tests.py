import shutil
import tempfile
from decimal import Decimal
from io import BytesIO

from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.test import TestCase, override_settings
from django.urls import reverse
from PIL import Image

from catalog.models import Category, Collection, Product, generate_variants


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




_TEMP_MEDIA = tempfile.mkdtemp()


@override_settings(MEDIA_ROOT=_TEMP_MEDIA)
class ImageVariantsTest(TestCase):
    """Automatic generation of resized webp/jpg image variants."""

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(_TEMP_MEDIA, ignore_errors=True)
        super().tearDownClass()

    def _make_source_image(self, name="products/test/sample.png", size=(800, 600)):
        # create a real PNG in memory and store it via default_storage
        buf = BytesIO()
        Image.new("RGB", size, (200, 120, 80)).save(buf, "PNG")
        buf.seek(0)
        return default_storage.save(name, ContentFile(buf.read()))

    def test_variants_are_generated_for_each_width(self):
        class Dummy:
            pass

        field = Dummy()
        field.name = self._make_source_image()

        generate_variants(field)

        stem = "products/test/sample"
        for width in (350, 525):
            for ext in ("jpg", "webp"):
                variant = f"{stem}-{width}w.{ext}"
                self.assertTrue(
                    default_storage.exists(variant),
                    f"Expected variant {variant} to be generated",
                )

    def test_generated_variant_has_correct_width(self):
        field = type("Dummy", (), {})()
        field.name = self._make_source_image(name="products/test/wide.png", size=(1000, 500))

        generate_variants(field)

        with default_storage.open("products/test/wide-350w.jpg", "rb") as f:
            img = Image.open(f)
            self.assertEqual(img.width, 350)

    def test_empty_image_field_is_ignored(self):
        # a field with no name should not raise
        field = type("Dummy", (), {})()
        field.name = ""
        try:
            generate_variants(field)
        except Exception as exc:
            self.fail(f"generate_variants raised unexpectedly: {exc}")


class CatalogFilterTest(TestCase):
    """product_list view filters by collection and category slugs."""

    def setUp(self):
        self.rings = Collection.objects.create(name="Rings")
        self.necklaces = Collection.objects.create(name="Necklaces")
        self.wedding = Category.objects.create(name="Wedding")
        self.casual = Category.objects.create(name="Casual")

        self.ring = Product.objects.create(
            collection=self.rings, category=self.wedding,
            name="Wedding Ring", price=Decimal("500"), sku="R-1",
        )
        self.necklace = Product.objects.create(
            collection=self.necklaces, category=self.casual,
            name="Casual Necklace", price=Decimal("300"), sku="N-1",
        )

    def test_no_filter_shows_all_products(self):
        response = self.client.get(reverse("catalog:list"))
        self.assertEqual(response.context["total_results"], 2)

    def test_filter_by_collection(self):
        response = self.client.get(reverse("catalog:list"), {"collection": "rings"})
        products = list(response.context["products"])
        self.assertIn(self.ring, products)
        self.assertNotIn(self.necklace, products)

    def test_filter_by_category(self):
        response = self.client.get(reverse("catalog:list"), {"category": "casual"})
        products = list(response.context["products"])
        self.assertIn(self.necklace, products)
        self.assertNotIn(self.ring, products)

    def test_inactive_product_is_hidden(self):
        self.ring.is_active = False
        self.ring.save()
        response = self.client.get(reverse("catalog:list"))
        self.assertEqual(response.context["total_results"], 1)
