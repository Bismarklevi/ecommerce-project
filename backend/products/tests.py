"""Covers the actual admin upload pipeline end to end (real form POST with a
real uploaded file), not just the model/serializer layer -- this is what
directly regression-guards "an image uploaded through the admin panel
renders on the frontend". See also cms/tests.py for the Banner equivalent.
"""
import io

from django.contrib.auth import get_user_model
from django.core.files.storage import default_storage
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from PIL import Image

from .models import Category, Product

User = get_user_model()


def make_test_image(name="test.jpg"):
    buf = io.BytesIO()
    Image.new("RGB", (100, 100), color="blue").save(buf, format="JPEG")
    buf.seek(0)
    return SimpleUploadedFile(name, buf.read(), content_type="image/jpeg")


class AdminImageUploadTests(TestCase):
    """Note: this deliberately doesn't fetch the resulting URL over HTTP --
    Django's static() media helper is wired up only when DEBUG=True (by
    design; production serves media via R2/a real web server instead), and
    that wiring happens once at urls.py import time, before any per-test
    settings override could take effect. What actually matters here, and
    what these assert instead, is that the upload really reached storage and
    that the API hands back a well-formed, absolute URL for it."""

    def setUp(self):
        self.staff = User.objects.create_superuser(username="staff", email="s@example.com", password="pw")
        self.client.force_login(self.staff)

    def test_category_image_uploaded_via_admin_reaches_storage_and_api(self):
        response = self.client.post(
            "/admin/products/category/add/",
            {
                "name": "Outerwear", "slug": "outerwear", "description": "",
                "image": make_test_image(), "image_url": "", "image_credit": "", "is_active": "on",
            },
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        category = Category.objects.get(slug="outerwear")
        self.assertTrue(category.image)
        self.assertTrue(default_storage.exists(category.image.name))

        api_response = self.client.get("/api/categories/")
        payload = next(row for row in api_response.json()["results"] if row["slug"] == "outerwear")
        self.assertTrue(payload["image"].startswith("http"))
        self.assertIn("category_images/", payload["image"])

    def test_product_image_uploaded_via_inline_reaches_storage_and_api(self):
        category = Category.objects.create(name="Menswear", slug="menswear")
        response = self.client.post(
            "/admin/products/product/add/",
            {
                "name": "Test Shirt", "slug": "test-shirt", "category": category.id,
                "description": "d", "base_price": "50.00", "is_featured": "", "is_active": "on",
                "variants-TOTAL_FORMS": "0", "variants-INITIAL_FORMS": "0",
                "variants-MIN_NUM_FORMS": "0", "variants-MAX_NUM_FORMS": "1000",
                "images-TOTAL_FORMS": "1", "images-INITIAL_FORMS": "0",
                "images-MIN_NUM_FORMS": "0", "images-MAX_NUM_FORMS": "1000",
                "images-0-image": make_test_image("shirt.jpg"),
                "images-0-alt_text": "Front view", "images-0-position": "0", "images-0-credit": "",
            },
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        product = Product.objects.get(slug="test-shirt")
        self.assertEqual(product.images.count(), 1)
        self.assertTrue(default_storage.exists(product.images.first().image.name))

        api_response = self.client.get("/api/products/")
        data = api_response.json()
        results = data.get("results", data) if isinstance(data, dict) else data
        payload = next(row for row in results if row["slug"] == "test-shirt")
        self.assertEqual(len(payload["images"]), 1)
        self.assertTrue(payload["images"][0]["image"].startswith("http"))


class VariantSizeOrderTests(TestCase):
    def test_variants_are_listed_in_garment_size_order(self):
        from decimal import Decimal

        from rest_framework.test import APIClient

        from .models import Category, Product, ProductVariant

        category = Category.objects.create(name="Dresses")
        product = Product.objects.create(
            category=category, name="Order Test Dress", description="d", base_price=Decimal("50.00")
        )
        for i, size in enumerate(["L", "XS", "M", "XL", "S"]):
            ProductVariant.objects.create(
                product=product, sku=f"ORD-{i}", size=size, color="Default",
                stock_quantity=1, price=Decimal("50.00"),
            )

        payload = APIClient().get("/api/products/").json()
        results = payload["results"] if isinstance(payload, dict) else payload
        match = next(p for p in results if p["name"] == "Order Test Dress")
        self.assertEqual([v["size"] for v in match["variants"]], ["XS", "S", "M", "L", "XL"])
