from datetime import timedelta
from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone

from app.models import Order, OrderItem, Payment
from products.models import Category, Product, ProductVariant

from .models import ReturnRequest

User = get_user_model()


class ReturnWindowTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="ret_buyer", email="r@example.com", password="pw")

    def _delivered_order(self, delivered_days_ago):
        order = Order.objects.create(user=self.user, total_amount=Decimal("100.00"))
        order.status = Order.STATUS_DELIVERED
        order.delivered_at = timezone.now() - timedelta(days=delivered_days_ago)
        order.save()
        return order

    def test_return_within_window_is_allowed(self):
        order = self._delivered_order(delivered_days_ago=5)
        request = ReturnRequest(order=order, reason="Wrong size")
        request.full_clean()  # must not raise

    def test_return_outside_window_is_rejected(self):
        order = self._delivered_order(delivered_days_ago=20)  # window is 14 days
        request = ReturnRequest(order=order, reason="Wrong size")
        with self.assertRaises(ValidationError):
            request.full_clean()

    def test_return_on_non_delivered_order_is_rejected(self):
        order = Order.objects.create(user=self.user, total_amount=Decimal("100.00"))  # still pending
        request = ReturnRequest(order=order, reason="Changed my mind")
        with self.assertRaises(ValidationError):
            request.full_clean()

    def test_approving_return_transitions_parent_order_to_returned(self):
        order = self._delivered_order(delivered_days_ago=1)
        request = ReturnRequest.objects.create(order=order, reason="Damaged item")
        request.transition_to(ReturnRequest.STATUS_APPROVED)
        order.refresh_from_db()
        self.assertEqual(order.status, Order.STATUS_RETURNED)


class RefundTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="refund_buyer", email="rf@example.com", password="pw")
        category = Category.objects.create(name="Menswear")
        product = Product.objects.create(category=category, name="Shirt", description="d", base_price=Decimal("100.00"))
        self.variant = ProductVariant.objects.create(
            product=product, sku="SKU-REFUND", size="M", color="Blue",
            stock_quantity=5, price=Decimal("100.00"),
        )
        self.order = Order.objects.create(user=self.user, total_amount=Decimal("100.00"))
        OrderItem.objects.create(
            order=self.order, product_variant=self.variant,
            product_name="Shirt", product_sku=self.variant.sku,
            size="M", color="Blue", quantity=1,
            unit_price=Decimal("100.00"), line_total=Decimal("100.00"),
        )
        self.payment = Payment.objects.create(
            order=self.order, provider="paystack", reference="refund-ref",
            amount=Decimal("100.00"), status=Payment.STATUS_SUCCESS,
        )
        self.order.status = Order.STATUS_DELIVERED
        self.order.payment_status = Order.PAYMENT_PAID
        self.order.delivered_at = timezone.now()
        self.order.save()

        self.request = ReturnRequest.objects.create(order=self.order, reason="Damaged", refund_amount=Decimal("100.00"))
        self.request.transition_to(ReturnRequest.STATUS_APPROVED)

    def test_failed_refund_does_not_change_any_local_state(self):
        # No PAYSTACK_SECRET_KEY / network in the test environment, so the
        # real call fails -- this must leave everything exactly as it was
        # rather than recording a refund that didn't actually happen.
        with self.assertRaises(ValueError):
            self.request.transition_to(ReturnRequest.STATUS_REFUNDED)

        self.request.refresh_from_db()
        self.payment.refresh_from_db()
        self.order.refresh_from_db()
        self.assertEqual(self.request.status, ReturnRequest.STATUS_APPROVED)
        self.assertEqual(self.payment.status, Payment.STATUS_SUCCESS)
        self.assertEqual(self.order.payment_status, Order.PAYMENT_PAID)

    def test_successful_refund_updates_return_payment_and_order(self):
        with patch("app.paystack.create_refund", return_value={"status": "processed", "id": 999}):
            self.request.transition_to(ReturnRequest.STATUS_REFUNDED)

        self.request.refresh_from_db()
        self.payment.refresh_from_db()
        self.order.refresh_from_db()
        self.assertEqual(self.request.status, ReturnRequest.STATUS_REFUNDED)
        self.assertEqual(self.payment.status, Payment.STATUS_REFUNDED)
        self.assertEqual(self.order.payment_status, Order.PAYMENT_REFUNDED)

    def test_cannot_refund_twice(self):
        with patch("app.paystack.create_refund", return_value={"status": "processed", "id": 999}):
            self.request.transition_to(ReturnRequest.STATUS_REFUNDED)

        with self.assertRaises(ValueError):
            self.request.transition_to(ReturnRequest.STATUS_REFUNDED)
