from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import resolve
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from products.models import Category, Product, ProductVariant

from .models import Order, OrderItem, Payment
from .services import (
    InsufficientStockError,
    mark_order_paid,
    reserve_stock_for_order,
)
from . import paystack

User = get_user_model()


def make_variant(stock=5, price="100.00"):
    category = Category.objects.create(name="Menswear")
    product = Product.objects.create(
        category=category, name="Test Shirt", description="d", base_price=Decimal(price)
    )
    return ProductVariant.objects.create(
        product=product, sku="SKU-1", size="M", color="Blue",
        stock_quantity=stock, price=Decimal(price),
    )


class OrderStateMachineTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="buyer", email="b@example.com", password="pw")
        self.order = Order.objects.create(user=self.user, total_amount=Decimal("100.00"))

    def test_valid_transition_succeeds(self):
        self.order.transition_to(Order.STATUS_PAID)
        self.assertEqual(self.order.status, Order.STATUS_PAID)

    def test_invalid_transition_is_rejected(self):
        # pending -> shipped is not a legal jump; must go through paid/processing first.
        with self.assertRaises(ValueError):
            self.order.transition_to(Order.STATUS_SHIPPED)
        self.assertEqual(self.order.status, Order.STATUS_PENDING)

    def test_terminal_state_accepts_no_further_transitions(self):
        self.order.transition_to(Order.STATUS_CANCELLED)
        with self.assertRaises(ValueError):
            self.order.transition_to(Order.STATUS_PAID)


class StockReservationTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="buyer2", email="b2@example.com", password="pw")
        self.variant = make_variant(stock=2)

    def _build_order(self, quantity):
        order = Order.objects.create(user=self.user, total_amount=Decimal("100.00") * quantity)
        OrderItem.objects.create(
            order=order, product_variant=self.variant,
            product_name="Test Shirt", product_sku=self.variant.sku,
            size="M", color="Blue", quantity=quantity,
            unit_price=Decimal("100.00"), line_total=Decimal("100.00") * quantity,
        )
        return order

    def test_reservation_decrements_stock(self):
        order = self._build_order(quantity=2)
        reserve_stock_for_order(order)
        self.variant.refresh_from_db()
        self.assertEqual(self.variant.stock_quantity, 0)

    def test_reservation_fails_when_insufficient_stock(self):
        order = self._build_order(quantity=3)  # only 2 in stock
        with self.assertRaises(InsufficientStockError):
            reserve_stock_for_order(order)
        self.variant.refresh_from_db()
        self.assertEqual(self.variant.stock_quantity, 2, "stock must be unchanged on failure")

    def test_second_concurrent_order_cannot_oversell_last_unit(self):
        self.variant.stock_quantity = 1
        self.variant.save()

        order_a = self._build_order(quantity=1)
        order_b = self._build_order(quantity=1)

        reserve_stock_for_order(order_a)  # succeeds, consumes the last unit
        with self.assertRaises(InsufficientStockError):
            reserve_stock_for_order(order_b)  # must fail — no stock left


class PaymentReconciliationTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="buyer3", email="b3@example.com", password="pw")
        self.order = Order.objects.create(user=self.user, total_amount=Decimal("50.00"))
        self.payment = Payment.objects.create(
            order=self.order, provider="paystack", reference="ref123", amount=Decimal("50.00")
        )

    def test_mark_order_paid_keeps_payment_and_order_in_sync(self):
        mark_order_paid(self.order, self.payment)
        self.order.refresh_from_db()
        self.payment.refresh_from_db()
        self.assertEqual(self.payment.status, Payment.STATUS_SUCCESS)
        self.assertEqual(self.order.payment_status, Order.PAYMENT_PAID)
        self.assertEqual(self.order.status, Order.STATUS_PAID)

    def test_mark_order_paid_persists_raw_response(self):
        # Regression test: raw_response was assigned in Python but left out
        # of save(update_fields=...) and silently never reached the database.
        mark_order_paid(self.order, self.payment, raw_response={"status": "success", "gateway_response": "Approved"})
        self.payment.refresh_from_db()
        self.assertEqual(self.payment.raw_response.get("gateway_response"), "Approved")


class OrderPaymentViewSetLockdownTests(TestCase):
    """A customer must never be able to rewrite or delete their own order or
    payment record after the fact -- these are the financial/audit trail.
    Regression coverage for a real bug found in QA: both viewsets were
    unrestricted ModelViewSets and a plain DELETE would erase an order."""

    def setUp(self):
        self.user = User.objects.create_user(username="lockdown_buyer", email="l@example.com", password="pw")
        self.order = Order.objects.create(user=self.user, total_amount=Decimal("10.00"), shipping_name="X")
        self.payment = Payment.objects.create(
            order=self.order, provider="paystack", reference="lockdown-ref", amount=Decimal("10.00")
        )
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def test_list_and_retrieve_still_work(self):
        self.assertEqual(self.client.get("/api/orders/").status_code, 200)
        self.assertEqual(self.client.get(f"/api/orders/{self.order.id}/").status_code, 200)
        self.assertEqual(self.client.get(f"/api/payments/{self.payment.id}/").status_code, 200)

    def test_order_cannot_be_patched_or_deleted(self):
        patch_resp = self.client.patch(
            f"/api/orders/{self.order.id}/", {"shipping_address": "HACKED"}, format="json"
        )
        delete_resp = self.client.delete(f"/api/orders/{self.order.id}/")
        self.assertEqual(patch_resp.status_code, 405)
        self.assertEqual(delete_resp.status_code, 405)
        self.assertTrue(Order.objects.filter(pk=self.order.id).exists())

    def test_payment_cannot_be_patched_or_deleted(self):
        patch_resp = self.client.patch(
            f"/api/payments/{self.payment.id}/", {"status": "success"}, format="json"
        )
        delete_resp = self.client.delete(f"/api/payments/{self.payment.id}/")
        self.assertEqual(patch_resp.status_code, 405)
        self.assertEqual(delete_resp.status_code, 405)


class WebhookRoutingTests(TestCase):
    def test_webhook_path_resolves_to_the_webhook_view_not_payment_detail(self):
        # Regression test for a critical bug: `path("api/", include(router.urls))`
        # was registered before the explicit webhook path, so DRF's router
        # swallowed /api/payments/webhook/ as PaymentViewSet's detail route
        # with pk="webhook" -- meaning Paystack's webhook was never actually
        # reachable. This must never regress silently.
        match = resolve("/api/payments/webhook/")
        self.assertEqual(match.url_name, "paystack-webhook")

    def test_payment_detail_route_is_unaffected(self):
        match = resolve("/api/payments/1/")
        self.assertEqual(match.url_name, "payment-detail")
        self.assertEqual(match.kwargs, {"pk": "1"})


class PaystackWebhookTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="webhook_buyer", email="w@example.com", password="pw")
        self.variant = make_variant(stock=3)
        self.order = Order.objects.create(user=self.user, total_amount=Decimal("100.00"))
        OrderItem.objects.create(
            order=self.order, product_variant=self.variant,
            product_name="Test Shirt", product_sku=self.variant.sku,
            size="M", color="Blue", quantity=1,
            unit_price=Decimal("100.00"), line_total=Decimal("100.00"),
        )
        reserve_stock_for_order(self.order)
        self.payment = Payment.objects.create(
            order=self.order, provider="paystack", reference="wh-ref", amount=Decimal("100.00")
        )
        self.client = APIClient()

    def _post_webhook(self, event, reference):
        import hashlib
        import hmac
        import json

        body = json.dumps({"event": event, "data": {"reference": reference}}).encode()
        with self.settings(PAYSTACK_SECRET_KEY="test-secret"):
            sig = hmac.new(b"test-secret", body, hashlib.sha512).hexdigest()
            return self.client.post(
                "/api/payments/webhook/", data=body, content_type="application/json",
                HTTP_X_PAYSTACK_SIGNATURE=sig,
            )

    def test_bad_signature_is_rejected(self):
        response = self.client.post(
            "/api/payments/webhook/", data=b'{"event":"charge.success","data":{"reference":"wh-ref"}}',
            content_type="application/json", HTTP_X_PAYSTACK_SIGNATURE="wrong",
        )
        self.assertEqual(response.status_code, 401)

    def test_unknown_reference_is_404(self):
        response = self._post_webhook("charge.success", "not-a-real-reference")
        self.assertEqual(response.status_code, 404)

    def test_charge_success_marks_order_paid(self):
        with patch.object(paystack, "verify_transaction", return_value={"status": "success"}):
            response = self._post_webhook("charge.success", "wh-ref")
        self.assertEqual(response.status_code, 200)
        self.order.refresh_from_db()
        self.payment.refresh_from_db()
        self.assertEqual(self.payment.status, Payment.STATUS_SUCCESS)
        self.assertEqual(self.order.status, Order.STATUS_PAID)

    def test_unhandled_event_type_is_ignored_not_treated_as_failure(self):
        # Regression test: any non-charge.success event used to be treated as
        # a failure, which would release stock on an unrelated event (e.g. a
        # dispute webhook) for an order that might already be shipped.
        response = self._post_webhook("charge.dispute.create", "wh-ref")
        self.assertEqual(response.status_code, 200)
        self.payment.refresh_from_db()
        self.variant.refresh_from_db()
        self.assertEqual(self.payment.status, Payment.STATUS_PENDING)
        self.assertEqual(self.variant.stock_quantity, 2, "stock reserved at checkout must be untouched")

    def test_stray_failure_after_success_cannot_downgrade_payment_or_release_stock(self):
        with patch.object(paystack, "verify_transaction", return_value={"status": "success"}):
            self._post_webhook("charge.success", "wh-ref")

        response = self._post_webhook("charge.failed", "wh-ref")

        self.assertEqual(response.status_code, 200)
        self.payment.refresh_from_db()
        self.order.refresh_from_db()
        self.variant.refresh_from_db()
        self.assertEqual(self.payment.status, Payment.STATUS_SUCCESS)
        self.assertEqual(self.order.payment_status, Order.PAYMENT_PAID)
        self.assertEqual(self.variant.stock_quantity, 2, "a paid order's stock must not be released")


class InvoicePDFTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="invoice_buyer", email="i@example.com", password="pw")
        self.order = Order.objects.create(
            user=self.user, total_amount=Decimal("100.00"),
            shipping_name="Kwaku \u201cCaf\u00e9\u201d \u00dcnicode \U0001F600",
            shipping_address="House \u2116 7, \u00d6tr\u00f6 Street \u2014 Accra",
        )
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def test_invoice_downloads_as_pdf(self):
        response = self.client.get(f"/api/orders/{self.order.id}/invoice/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/pdf")

    def test_invoice_survives_non_latin1_characters(self):
        # Regression test: fpdf2's core fonts only support Latin-1, and an
        # em dash in the template alone used to crash this with a 500.
        response = self.client.get(f"/api/orders/{self.order.id}/invoice/")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.content.startswith(b"%PDF"))

    def test_invoice_is_scoped_to_owner(self):
        other = User.objects.create_user(username="invoice_other", email="io@example.com", password="pw")
        other_client = APIClient()
        other_client.force_authenticate(other)
        response = other_client.get(f"/api/orders/{self.order.id}/invoice/")
        self.assertEqual(response.status_code, 404)
