import json
import logging

from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import mixins, permissions, serializers, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView

from products.models import ProductVariant

from . import paystack
from .invoices import generate_invoice_pdf
from .models import Cart, CartItem, Order, Payment
from .serializers import CartItemSerializer, CartSerializer, OrderSerializer, PaymentSerializer
from .services import mark_order_paid, mark_order_payment_failed

logger = logging.getLogger(__name__)


class CheckoutInitResponseSerializer(serializers.Serializer):
    authorization_url = serializers.URLField()
    access_code = serializers.CharField()
    reference = serializers.CharField()
    order_id = serializers.IntegerField()


class CheckoutErrorSerializer(serializers.Serializer):
    detail = serializers.CharField()


class CartViewSet(viewsets.ModelViewSet):
    serializer_class = CartSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return (
            Cart.objects.filter(user=self.request.user)
            .prefetch_related("items__product_variant__product", "items__product_variant__product__category")
            .select_related("user")
        )

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def _get_or_create_cart(self, request):
        cart, _ = Cart.objects.get_or_create(user=request.user)
        return cart

    @extend_schema(
        tags=["Cart"],
        summary="Get (or create) the signed-in user's cart",
        responses={200: CartSerializer},
    )
    @action(detail=False, methods=["get"], url_path="mine")
    def mine(self, request):
        cart = self._get_or_create_cart(request)
        serializer = self.get_serializer(cart)
        return Response(serializer.data)

    @extend_schema(
        tags=["Cart"],
        summary="Add a product variant to the signed-in user's cart (creates the cart if needed)",
        responses={200: CartSerializer, 400: None, 404: None},
    )
    @action(detail=False, methods=["post"], url_path="add-item")
    def add_item(self, request):
        variant_id = request.data.get("product_variant_id")
        try:
            quantity = int(request.data.get("quantity", 1))
        except (TypeError, ValueError):
            return Response({"detail": "quantity must be a whole number."}, status=status.HTTP_400_BAD_REQUEST)
        if quantity < 1:
            return Response({"detail": "quantity must be at least 1."}, status=status.HTTP_400_BAD_REQUEST)

        variant = get_object_or_404(ProductVariant, pk=variant_id)
        cart = self._get_or_create_cart(request)

        item, created = CartItem.objects.get_or_create(
            cart=cart, product_variant=variant, defaults={"quantity": quantity}
        )
        if not created:
            item.quantity += quantity
            item.save(update_fields=["quantity", "updated_at"])

        serializer = self.get_serializer(cart)
        return Response(serializer.data)


class CartItemViewSet(mixins.UpdateModelMixin, viewsets.GenericViewSet):
    """Update quantity or remove a single line item. Scoped to the signed-in
    user's own cart -- get_queryset is the only thing standing between this and
    letting anyone edit anyone else's cart by guessing an id."""

    serializer_class = CartItemSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return CartItem.objects.filter(cart__user=self.request.user).select_related(
            "cart", "product_variant__product"
        )

    def _cart_response(self, cart):
        cart_serializer = CartSerializer(cart, context=self.get_serializer_context())
        return Response(cart_serializer.data)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return self._cart_response(instance.cart)

    @extend_schema(
        tags=["Cart"],
        summary="Remove a line item from the signed-in user's cart",
        responses={200: CartSerializer, 404: None},
    )
    @action(detail=True, methods=["delete"], url_path="remove")
    def remove(self, request, pk=None):
        item = self.get_object()
        cart = item.cart
        item.delete()
        return self._cart_response(cart)


class OrderViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, mixins.CreateModelMixin, viewsets.GenericViewSet):
    """Deliberately excludes update/destroy. An order is the record of a
    transaction -- once placed, a customer being able to rewrite its shipping
    details (post-delivery, no less) or delete it outright would falsify that
    record and destroy order history a business needs for support, disputes,
    and accounting. Any legitimate post-creation change (cancellation,
    address correction while still pending, admin re-ship) goes through a
    dedicated, audited action instead of a bare PATCH/DELETE on the resource."""

    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return (
            Order.objects.filter(user=self.request.user)
            .select_related("user")
            .prefetch_related("items__product_variant__product", "payment")
        )

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @extend_schema(
        tags=["Orders"],
        summary="Download a PDF invoice for this order",
        responses={200: OpenApiResponse(description="application/pdf")},
    )
    @action(detail=True, methods=["get"], url_path="invoice")
    def invoice(self, request, pk=None):
        order = self.get_object()
        pdf_bytes = generate_invoice_pdf(order)
        response = HttpResponse(pdf_bytes, content_type="application/pdf")
        response["Content-Disposition"] = f'attachment; filename="kaira-invoice-{order.id}.pdf"'
        return response


class PaymentViewSet(viewsets.ReadOnlyModelViewSet):
    """Read-only: PaystackWebhookView is the only path that ever writes to a
    Payment (see mark_order_paid / mark_order_payment_failed in services.py),
    and that's deliberate -- a customer being able to edit their own payment's
    status or amount, or delete the record, would let them fake a refund or
    erase the transaction history a dispute would need."""

    serializer_class = PaymentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Payment.objects.filter(order__user=self.request.user).select_related("order")


class CheckoutView(APIView):
    """Initiates payment for a pending order. This never marks an order as paid
    itself — only PaystackWebhookView does that, from a signed server-to-server
    callback, so a client can never fake "payment successful" from the browser."""

    permission_classes = [permissions.IsAuthenticated]
    # Authenticated, so this throttle keys on the user id -- caps how fast one
    # account can spin up Paystack transactions.
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "payment"

    @extend_schema(
        tags=["Payments"],
        summary="Initiate Paystack checkout for a pending order",
        request=None,
        responses={
            200: CheckoutInitResponseSerializer,
            409: OpenApiResponse(CheckoutErrorSerializer, description="Order already paid/checked out"),
            502: OpenApiResponse(CheckoutErrorSerializer, description="Paystack initialization failed"),
        },
    )
    def post(self, request, order_id, *args, **kwargs):
        order = get_object_or_404(Order, pk=order_id, user=request.user)

        if order.status != Order.STATUS_PENDING:
            return Response(
                {"detail": f"Order is '{order.status}' and cannot be checked out again."},
                status=status.HTTP_409_CONFLICT,
            )

        payment, created = Payment.objects.get_or_create(
            order=order,
            defaults={
                "provider": "paystack",
                "reference": paystack.generate_reference(),
                "amount": order.total_amount,
            },
        )
        if not created and payment.status == Payment.STATUS_SUCCESS:
            return Response({"detail": "Order is already paid."}, status=status.HTTP_409_CONFLICT)

        try:
            result = paystack.initialize_transaction(
                email=order.shipping_email or request.user.email,
                amount_pesewas=int(order.total_amount * 100),
                reference=payment.reference,
                callback_url=f"{settings.FRONTEND_URL}/checkout/success?order_id={order.id}",
            )
        except paystack.PaystackError as exc:
            logger.error("Paystack initialization failed for order %s: %s", order.id, exc)
            return Response({"detail": str(exc)}, status=status.HTTP_502_BAD_GATEWAY)

        order.payment_status = Order.PAYMENT_PENDING
        order.save(update_fields=["payment_status", "updated_at"])

        return Response(
            {
                "authorization_url": result["authorization_url"],
                "access_code": result["access_code"],
                "reference": payment.reference,
                "order_id": order.id,
            }
        )


class PaystackWebhookView(APIView):
    """Server-to-server callback — the single source of truth for payment success.
    Client-reported "payment complete" is never trusted (see CheckoutView docstring)."""

    permission_classes = [permissions.AllowAny]
    authentication_classes = []
    # Paystack retries deliver from its own IPs and can burst; the HMAC signature
    # check is the real gate here, so don't rate-limit legitimate retries away.
    throttle_classes = []

    @extend_schema(
        tags=["Payments"],
        summary="Paystack webhook (server-to-server, HMAC-SHA512 signed)",
        request=None,
        responses={200: None, 400: None, 401: None, 404: None, 502: None},
    )
    def post(self, request, *args, **kwargs):
        signature = request.headers.get("X-Paystack-Signature", "")
        if not paystack.verify_webhook_signature(request.body, signature):
            logger.warning("Rejected Paystack webhook with invalid signature.")
            return Response(status=status.HTTP_401_UNAUTHORIZED)

        payload = json.loads(request.body or "{}")
        event = payload.get("event")
        data = payload.get("data", {})
        reference = data.get("reference")

        if not reference:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        # Paystack's webhook fires for many event types (transfers, disputes,
        # subscriptions...), some of which can carry this same `reference` in
        # their payload without being about this charge's success/failure at
        # all. Only react to the two charge events this endpoint is actually
        # built to handle -- anything else is acknowledged (200, so Paystack
        # doesn't retry it forever) and otherwise ignored, rather than falling
        # through to "treat as failed" and potentially releasing stock on a
        # perfectly fine, already-fulfilled order.
        if event not in ("charge.success", "charge.failed"):
            logger.info("Ignoring unhandled Paystack webhook event '%s' for reference %s", event, reference)
            return Response(status=status.HTTP_200_OK)

        try:
            payment = Payment.objects.select_related("order").get(reference=reference)
        except Payment.DoesNotExist:
            logger.warning("Webhook for unknown payment reference: %s", reference)
            return Response(status=status.HTTP_404_NOT_FOUND)

        # A payment that already succeeded is done -- further webhooks for the
        # same reference (redelivery, or a stray/out-of-order 'failed' event)
        # must never re-verify-and-possibly-downgrade it. Re-verifying is also
        # simply unnecessary at that point: Paystack's own record of a
        # completed charge doesn't change after the fact.
        if payment.status == Payment.STATUS_SUCCESS:
            return Response(status=status.HTTP_200_OK)

        # Re-verify server-side with Paystack directly rather than trusting the
        # webhook body's own "status" field — the webhook proves *a* callback
        # happened, verify_transaction proves it's genuinely settled.
        try:
            verified = paystack.verify_transaction(reference)
        except paystack.PaystackError as exc:
            logger.error("Could not verify Paystack transaction %s: %s", reference, exc)
            return Response(status=status.HTTP_502_BAD_GATEWAY)

        if event == "charge.success" and verified.get("status") == "success":
            mark_order_paid(payment.order, payment, raw_response=verified)
        else:
            mark_order_payment_failed(payment.order, payment, reason=verified.get("gateway_response", ""))

        return Response(status=status.HTTP_200_OK)

