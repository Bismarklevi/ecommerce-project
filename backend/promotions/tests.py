from datetime import timedelta
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone
from unittest.mock import patch
from django.contrib.auth import get_user_model
from django.core.cache import cache
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient
from app.models import Order, Payment
from .models import Coupon, CouponRedemption

User = get_user_model()


def make_coupon(**overrides):
    defaults = dict(
        code="SAVE10", discount_type=Coupon.TYPE_PERCENTAGE, value=Decimal("10"),
        valid_from=timezone.now() - timedelta(days=1),
        valid_until=timezone.now() + timedelta(days=1),
    )
    defaults.update(overrides)
    return Coupon.objects.create(**defaults)


class CouponDiscountTests(TestCase):
    def test_percentage_discount_never_exceeds_subtotal(self):
        coupon = make_coupon(discount_type=Coupon.TYPE_PERCENTAGE, value=Decimal("150"))
        # Even a (misconfigured) >100% coupon must not discount more than the order itself.
        discount = coupon.compute_discount(Decimal("100.00"))
        self.assertLessEqual(discount, Decimal("100.00"))

    def test_max_discount_amount_caps_percentage_coupon(self):
        coupon = make_coupon(
            discount_type=Coupon.TYPE_PERCENTAGE, value=Decimal("50"),
            max_discount_amount=Decimal("20.00"),
        )
        discount = coupon.compute_discount(Decimal("1000.00"))  # 50% would be 500
        self.assertEqual(discount, Decimal("20.00"))

    def test_expired_coupon_fails_validation(self):
        coupon = make_coupon(
            valid_from=timezone.now() - timedelta(days=10),
            valid_until=timezone.now() - timedelta(days=1),
        )
        with self.assertRaises(ValidationError):
            coupon.validate_for(user=None, order_subtotal=Decimal("100.00"))

    def test_usage_limit_reached_fails_validation(self):
        coupon = make_coupon(usage_limit=1, times_used=1)
        with self.assertRaises(ValidationError):
            coupon.validate_for(user=None, order_subtotal=Decimal("100.00"))

    def test_below_minimum_order_fails_validation(self):
        coupon = make_coupon(min_order_amount=Decimal("200.00"))
        with self.assertRaises(ValidationError):
            coupon.validate_for(user=None, order_subtotal=Decimal("100.00"))


def fake_init(**kwargs):
    return {"authorization_url": "https://pay.example/x", "access_code": "ac", "reference": kwargs["reference"]}


class CouponCheckoutTests(TestCase):
    def setUp(self):
        cache.clear()  # throttles are cache-backed; keep test order irrelevant
        self.user = User.objects.create_user(username="couponuser", email="c@example.com", password="pw")
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {Token.objects.create(user=self.user).key}")
        self.order = Order.objects.create(
            user=self.user, total_amount=Decimal("100.00"), shipping_email="c@example.com"
        )
        now = timezone.now()
        self.coupon = Coupon.objects.create(
            code="TEN",
            discount_type=Coupon.TYPE_PERCENTAGE,
            value=Decimal("10"),
            valid_from=now - timedelta(days=1),
            valid_until=now + timedelta(days=1),
        )
        self.url = f"/api/orders/{self.order.id}/checkout/"

    @patch("app.views.paystack.initialize_transaction", side_effect=fake_init)
    def test_checkout_applies_coupon_and_charges_discounted_total(self, init):
        response = self.client.post(self.url, {"coupon_code": "ten"}, format="json")
        self.assertEqual(response.status_code, 200, response.content)

        self.order.refresh_from_db()
        self.assertEqual(self.order.total_amount, Decimal("90.00"))
        self.assertEqual(init.call_args.kwargs["amount_pesewas"], 9000)
        self.assertEqual(Payment.objects.get(order=self.order).amount, Decimal("90.00"))
        self.assertEqual(response.json()["discount_amount"], "10.00")
        self.assertEqual(response.json()["amount"], "90.00")

        self.assertEqual(CouponRedemption.objects.filter(order=self.order).count(), 1)
        self.coupon.refresh_from_db()
        self.assertEqual(self.coupon.times_used, 1)

    @patch("app.views.paystack.initialize_transaction", side_effect=fake_init)
    def test_checkout_retry_with_same_code_does_not_discount_twice(self, init):
        self.client.post(self.url, {"coupon_code": "TEN"}, format="json")
        response = self.client.post(self.url, {"coupon_code": "TEN"}, format="json")
        self.assertEqual(response.status_code, 200, response.content)

        self.order.refresh_from_db()
        self.assertEqual(self.order.total_amount, Decimal("90.00"))
        self.coupon.refresh_from_db()
        self.assertEqual(self.coupon.times_used, 1)
        self.assertEqual(CouponRedemption.objects.count(), 1)

    @patch("app.views.paystack.initialize_transaction", side_effect=fake_init)
    def test_unknown_code_is_refused_before_payment_is_touched(self, init):
        response = self.client.post(self.url, {"coupon_code": "NOPE"}, format="json")
        self.assertEqual(response.status_code, 400)
        self.assertIn("not found", response.json()["detail"].lower())
        init.assert_not_called()
        self.order.refresh_from_db()
        self.assertEqual(self.order.total_amount, Decimal("100.00"))
        self.assertFalse(Payment.objects.filter(order=self.order).exists())

    @patch("app.views.paystack.initialize_transaction", side_effect=fake_init)
    def test_checkout_without_code_is_unchanged(self, init):
        response = self.client.post(self.url, {}, format="json")
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(response.json()["discount_amount"], "0.00")
        self.order.refresh_from_db()
        self.assertEqual(self.order.total_amount, Decimal("100.00"))

    def test_validate_endpoint_previews_without_redeeming(self):
        response = self.client.post(
            "/api/promotions/validate/", {"code": "TEN", "order_subtotal": "100.00"}, format="json"
        )
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(response.json()["discount_amount"], "10.00")
        self.assertEqual(CouponRedemption.objects.count(), 0)
        self.coupon.refresh_from_db()
        self.assertEqual(self.coupon.times_used, 0)
