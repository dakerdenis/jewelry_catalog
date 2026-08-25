# -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand

from catalog.models import ProductImage
from catalog.utils.image_variants import generate_variants


class Command(BaseCommand):
    help = "Generate resized JPG/WebP variants for all product images"

    def handle(self, *args, **opts):
        qs = ProductImage.objects.all().select_related("product")
        total = qs.count()
        ok = 0
        for img in qs.iterator():
            try:
                generate_variants(img.image)
                ok += 1
            except Exception as e:
                self.stderr.write(f"[skip] {img.id}: {e}")
        self.stdout.write(self.style.SUCCESS(f"Done: {ok}/{total} images processed"))
