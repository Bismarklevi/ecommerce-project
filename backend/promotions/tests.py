from datetime import timedelta
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone
from .models import Coupon


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
