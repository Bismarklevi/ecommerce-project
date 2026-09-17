from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import F

from .models import Coupon, CouponRedemption


@transaction.atomic
def apply_coupon_to_order(order, code: str, user) -> Decimal:
    """Redeem `code` against `order`: record the redemption, bump the coupon's
    usage counter and reduce order.total_amount. Returns the discount applied.

    Idempotent per order: calling again with the same code (a checkout retry
    after a failed payment init) returns the existing discount without
    discounting twice. A different code on an order that already has one is
    refused -- swapping would need the first redemption unwound, which is a
    support action, not something a retry should do silently.

    Raises django ValidationError with a user-facing message on any refusal.
    The caller is expected to hold this inside the same transaction as
    payment initiation so a code is only ever consumed by an order that
    actually reached the payment provider.
    """
    code = (code or "").strip()
    if not code:
        raise ValidationError("Enter a promo code.")

    existing = (
        CouponRedemption.objects.select_related("coupon").filter(order=order).first()
    )
    if existing is not None:
        if existing.coupon.code.lower() == code.lower():
            return existing.discount_amount
        raise ValidationError("A different promo code has already been applied to this order.")

    try:
        # Row lock: two concurrent redemptions of a coupon at its usage limit
        # must not both pass validate_for().
        coupon = Coupon.objects.select_for_update().get(code__iexact=code)
    except Coupon.DoesNotExist as exc:
        raise ValidationError("Promo code not found.") from exc

    subtotal = order.total_amount
    coupon.validate_for(user=user, order_subtotal=subtotal)
    discount = coupon.compute_discount(subtotal)

    CouponRedemption.objects.create(
        coupon=coupon, user=user, order=order, discount_amount=discount
    )
    Coupon.objects.filter(pk=coupon.pk).update(times_used=F("times_used") + 1)

    order.total_amount = subtotal - discount
    order.save(update_fields=["total_amount", "updated_at"])
    return discount
