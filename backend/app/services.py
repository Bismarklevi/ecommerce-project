"""Order/payment business logic.

Kept separate from serializers and views deliberately: this is the layer that has
to be correct under concurrency (two customers buying the last unit at once) and
correct against an external system (Paystack), so it gets its own tests and isn't
tangled with HTTP request/response shaping.
"""
import logging
from decimal import Decimal

from django.db import transaction
from django.db.models import F

from products.models import ProductVariant

from .models import Order, Payment

logger = logging.getLogger(__name__)


class InsufficientStockError(Exception):
    def __init__(self, variant: ProductVariant, requested: int):
        self.variant = variant
        self.requested = requested
        super().__init__(
            f"Only {variant.stock_quantity} unit(s) left for {variant}, "
            f"but {requested} were requested."
        )


@transaction.atomic
def reserve_stock_for_order(order: Order) -> None:
    """Atomically decrements ProductVariant stock for every item on `order`.

    Uses select_for_update so two concurrent checkouts on the last unit of a variant
    cannot both succeed — the second request re-reads the row after the first
    transaction commits and sees the decremented (or zero) quantity. This is what
    "no overselling under concurrent orders" actually requires; checking stock in a
    serializer without locking the row is a race condition, not a guarantee.
    """
    for item in order.items.select_related("product_variant").all():
        variant = ProductVariant.objects.select_for_update().get(pk=item.product_variant_id)
        if variant.stock_quantity < item.quantity:
            raise InsufficientStockError(variant, item.quantity)
        variant.stock_quantity -= item.quantity
        variant.save(update_fields=["stock_quantity", "updated_at"])


@transaction.atomic
def release_stock_for_order(order: Order) -> None:
    """Returns reserved stock to inventory — used on cancellation/return."""
    for item in order.items.select_related("product_variant").all():
        variant = ProductVariant.objects.select_for_update().get(pk=item.product_variant_id)
        variant.stock_quantity += item.quantity
        variant.save(update_fields=["stock_quantity", "updated_at"])


@transaction.atomic
def apply_coupon_to_order(order: Order, coupon, user) -> Decimal:
    """Validates and redeems a coupon against an order in one atomic step, so a
    coupon can never be "previewed valid" and then redeemed twice, or redeemed
    against an order whose subtotal changed between preview and checkout."""
    from promotions.models import CouponRedemption

    coupon.validate_for(user=user, order_subtotal=order.total_amount)
    discount = coupon.compute_discount(order.total_amount)

    CouponRedemption.objects.create(
        coupon=coupon, user=user if user and user.is_authenticated else None,
        order=order, discount_amount=discount,
    )
    # F() avoids a lost-update race if two orders redeem the same coupon in the
    # same instant — the increment happens in the database, not in Python.
    coupon.__class__.objects.filter(pk=coupon.pk).update(times_used=F("times_used") + 1)
    order.total_amount = order.total_amount - discount
    order.save(update_fields=["total_amount"])
    return discount


@transaction.atomic
def mark_order_paid(order: Order, payment: Payment, raw_response: dict | None = None) -> None:
    """Reconciles a successful payment: flips payment + order status together so
    they can never disagree (e.g. payment=success but order still 'pending').
    Safe to call more than once for the same payment (Paystack redelivers
    webhooks) -- transition_to only fires when the order is still pending, so
    a retry is a no-op rather than a duplicate status-change notification."""
    payment.status = Payment.STATUS_SUCCESS
    update_fields = ["status", "updated_at"]
    if raw_response is not None:
        payment.raw_response = raw_response
        update_fields.append("raw_response")
    payment.save(update_fields=update_fields)

    order.payment_status = Order.PAYMENT_PAID
    order.save(update_fields=["payment_status", "updated_at"])
    if order.status == Order.STATUS_PENDING:
        order.transition_to(Order.STATUS_PAID)


@transaction.atomic
def flag_payment_for_review(
    order: Order,
    payment: Payment,
    *,
    expected_pesewas: int,
    actual_pesewas: int | None,
    actual_currency: str | None,
    raw_response: dict,
) -> None:
    """Paystack confirmed the charge succeeded, but the amount and/or currency
    it confirms don't match what this order expects -- per Paystack's own
    integration guidance, the webhook body and even a verify_transaction
    response must never be trusted on amount alone. This never happens for a
    normal declined card (that's charge.failed, handled separately) or a
    normal successful payment; when it does happen, it means either a bug
    upstream of this check, a stale/mismatched reference somehow reaching
    this webhook, or an active manipulation attempt. Any of those wants a
    human looking at it before the order is fulfilled -- not an automated
    "close enough" acceptance, and not an automated cancellation that could
    be wrong the other way if this is actually a legitimate case with a
    reference collision.

    Logged at CRITICAL specifically so this is impossible to miss in
    production log monitoring/alerting -- a mismatched payment amount is a
    financial-integrity event, not a routine warning.
    """
    logger.critical(
        "PAYMENT AMOUNT/CURRENCY MISMATCH: order=%s payment=%s reference=%s "
        "expected_pesewas=%s actual_pesewas=%s actual_currency=%s -- "
        "payment flagged for manual review, order NOT marked paid.",
        order.id, payment.id, payment.reference,
        expected_pesewas, actual_pesewas, actual_currency,
    )
    payment.status = Payment.STATUS_FLAGGED
    payment.raw_response = raw_response
    payment.save(update_fields=["status", "raw_response", "updated_at"])
    # order.status/payment_status and stock are deliberately left untouched --
    # see docstring. A staff member resolves this from the admin after
    # checking the real transaction in the Paystack dashboard.


@transaction.atomic
def mark_order_payment_failed(order: Order, payment: Payment, reason: str = "") -> None:
    """Only ever call this for a payment that hasn't already succeeded. A stray
    or out-of-order 'failed' webhook arriving after the real 'success' one
    (Paystack delivery is at-least-once, not guaranteed-ordered) must never be
    allowed to knock a paid/shipped order back to failed and release its
    stock -- see PaystackWebhookView, which enforces this before calling in."""
    if payment.status == Payment.STATUS_SUCCESS:
        return

    payment.status = Payment.STATUS_FAILED
    payment.raw_response = {**payment.raw_response, "failure_reason": reason}
    payment.save(update_fields=["status", "raw_response", "updated_at"])

    order.payment_status = Order.PAYMENT_FAILED
    order.save(update_fields=["payment_status", "updated_at"])
    # Stock reserved at order-creation time is released on payment failure so it
    # isn't locked up indefinitely by an abandoned/failed checkout.
    release_stock_for_order(order)


@transaction.atomic
def refund_order_payment(order: Order, *, amount: Decimal | None = None) -> dict:
    """Issues a real Paystack refund for `order`'s payment and reconciles local
    state to match. Raises paystack.PaystackError if Paystack rejects the
    refund (insufficient settled balance, already refunded, etc.) -- in that
    case nothing local changes, so a failed refund attempt can safely be
    retried rather than leaving Order/Payment in a state that claims a refund
    happened when it didn't.

    Called from ReturnRequest.transition_to() when a return is marked
    refunded (see returns/models.py) -- refunding is the one return outcome
    that has to reach an external system, so it can't be "just a status
    field" the way approve/reject are.
    """
    from . import paystack

    payment = order.payment
    if payment.status != Payment.STATUS_SUCCESS:
        raise ValueError(f"Cannot refund order {order.id}: its payment is '{payment.status}', not 'success'.")

    amount_pesewas = int(amount * 100) if amount is not None else None
    result = paystack.create_refund(reference=payment.reference, amount_pesewas=amount_pesewas)

    payment.status = Payment.STATUS_REFUNDED
    payment.raw_response = {**payment.raw_response, "refund": result}
    payment.save(update_fields=["status", "raw_response", "updated_at"])

    order.payment_status = Order.PAYMENT_REFUNDED
    order.save(update_fields=["payment_status", "updated_at"])

    return result
