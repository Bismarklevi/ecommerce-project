"""Tests for the data-subject rights endpoints (export + erasure)."""

from decimal import Decimal

from django.contrib.auth import get_user_model
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient, APITestCase

from app.models import Order, OrderItem
from products.models import Category, Product, ProductVariant
from wishlist.models import WishlistItem

User = get_user_model()


def _make_variant():
    category = Category.objects.create(name="Dresses")
    product = Product.objects.create(
        category=category, name="Silk Dress", description="d", base_price=Decimal("200.00")
    )
    variant = ProductVariant.objects.create(
        product=product, sku="SKU-D", size="M", color="Cream",
        stock_quantity=5, price=Decimal("200.00"),
    )
    return product, variant


class PersonalDataExportTests(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="dataowner", email="owner@example.com", password="Correct123!",
            first_name="Ama", phone_number="0244000000",
        )
        self.client.force_authenticate(self.user)

        self.product, self.variant = _make_variant()
        self.user.addresses.create(
            label="Home", full_name="Ama Owusu", address_line1="1 High St", city="Accra",
        )
        order = Order.objects.create(
            user=self.user, total_amount=Decimal("200.00"),
            shipping_name="Ama Owusu", shipping_email="owner@example.com",
        )
        OrderItem.objects.create(
            order=order, product_variant=self.variant, product_name="Silk Dress",
            product_sku="SKU-D", size="M", color="Cream", quantity=1,
            unit_price=Decimal("200.00"), line_total=Decimal("200.00"),
        )
        self.product.reviews.create(user=self.user, rating=5, body="Lovely.")
        WishlistItem.objects.create(user=self.user, product=self.product)

    def test_export_includes_all_personal_data(self):
        response = self.client.get("/api/me/export/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("attachment", response["Content-Disposition"])

        data = response.json()
        self.assertEqual(data["account"]["email"], "owner@example.com")
        self.assertEqual(len(data["addresses"]), 1)
        self.assertEqual(len(data["orders"]), 1)
        self.assertEqual(data["orders"][0]["items"][0]["product_name"], "Silk Dress")
        self.assertEqual(len(data["reviews"]), 1)
        self.assertEqual(len(data["wishlist"]), 1)

    def test_export_requires_authentication(self):
        self.client.force_authenticate(None)
        self.assertEqual(self.client.get("/api/me/export/").status_code, 401)

    def test_export_returns_only_the_requesters_data(self):
        other = User.objects.create_user(username="intruder", email="x@example.com", password="pw")
        other.addresses.create(full_name="Someone Else", address_line1="9 Other Rd", city="Kumasi")
        data = self.client.get("/api/me/export/").json()
        names = [a["full_name"] for a in data["addresses"]]
        self.assertNotIn("Someone Else", names)


class AccountDeletionTests(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="leaver", email="leaver@example.com", password="Correct123!",
        )
        self.client.force_authenticate(self.user)
        self.product, self.variant = _make_variant()
        self.user.addresses.create(full_name="Kofi", address_line1="2 Main St", city="Accra")
        self.order = Order.objects.create(
            user=self.user, total_amount=Decimal("200.00"),
            shipping_name="Kofi Mensah", shipping_email="leaver@example.com",
            shipping_phone="0244111111", shipping_address="2 Main St, Accra",
        )
        self.product.reviews.create(user=self.user, rating=4, body="Good.")
        WishlistItem.objects.create(user=self.user, product=self.product)

    def test_wrong_password_does_not_delete(self):
        response = self.client.post("/api/me/delete/", {"password": "nope"}, format="json")
        self.assertEqual(response.status_code, 400)
        self.user.refresh_from_db()
        self.assertTrue(self.user.is_active)
        self.assertEqual(self.user.email, "leaver@example.com")

    def test_correct_password_anonymizes_and_retains_orders(self):
        response = self.client.post("/api/me/delete/", {"password": "Correct123!"}, format="json")
        self.assertEqual(response.status_code, 204)

        self.user.refresh_from_db()
        # Account scrubbed and locked.
        self.assertFalse(self.user.is_active)
        self.assertTrue(self.user.username.startswith("deleted_"))
        self.assertNotEqual(self.user.email, "leaver@example.com")
        self.assertFalse(self.user.has_usable_password())

        # Non-retained personal data is gone.
        self.assertEqual(self.user.addresses.count(), 0)
        self.assertEqual(self.user.reviews.count(), 0)
        self.assertEqual(self.user.wishlist_items.count(), 0)
        self.assertFalse(Token.objects.filter(user=self.user).exists())

        # The order is retained (legal record) but scrubbed of identifying detail.
        self.order.refresh_from_db()
        self.assertEqual(self.order.shipping_name, "[deleted]")
        self.assertEqual(self.order.shipping_email, "")
        self.assertEqual(self.order.shipping_phone, "")
        self.assertEqual(self.order.total_amount, Decimal("200.00"))

    def test_deletion_requires_authentication(self):
        self.client.force_authenticate(None)
        self.assertEqual(
            self.client.post("/api/me/delete/", {"password": "Correct123!"}, format="json").status_code,
            401,
        )
