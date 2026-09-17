from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import models


class Coupon(models.Model):
    TYPE_PERCENTAGE = "percentage"
    TYPE_FLAT = "flat"
    TYPE_CHOICES = [
        (TYPE_PERCENTAGE, "Percentage off"),
        (TYPE_FLAT, "Flat amount off"),
    ]

    code = models.CharField(max_length=32, unique=True)
    discount_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default=TYPE_PERCENTAGE)
    # Percentage: 0-100. Flat: currency amount. Kept as one field with a validator per type
    # in clean() rather than two nullable fields, since exactly one is ever meaningful.
    value = models.DecimalField(max_digits=10, decimal_places=2)
    # Hard floor so a coupon can never discount an order below cost — this is the
    # margin-aware guardrail called out in the business-logic requirements.
    max_discount_amount = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True,
        help_text="Optional cap on the absolute discount, regardless of percentage/order size.",
    )
    min_order_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    usage_limit = models.PositiveIntegerField(
        null=True, blank=True, help_text="Total redemptions allowed across all customers. Blank = unlimited.",
    )
    times_used = models.PositiveIntegerField(default=0)
    per_user_limit = models.PositiveIntegerField(default=1)
    is_active = models.BooleanField(default=True)
    valid_from = models.DateTimeField()
    valid_until = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def clean(self):
        if self.discount_type == self.TYPE_PERCENTAGE and (self.value <= 0 or self.value > 100):
            raise ValidationError("Percentage coupons must have a value between 0 and 100.")
        if self.discount_type == self.TYPE_FLAT and self.value <= 0:
            raise ValidationError("Flat-amount coupons must have a positive value.")
        if self.valid_until <= self.valid_from:
            raise ValidationError("valid_until must be after valid_from.")

    def __str__(self):
        return self.code

    def compute_discount(self, order_subtotal: Decimal) -> Decimal:
        """Pure calculation — does not mutate usage counters. Never returns more than
        the order subtotal itself, so a coupon can never make a line item negative."""
        if self.discount_type == self.TYPE_PERCENTAGE:
            discount = order_subtotal * (self.value / Decimal("100"))
        else:
            discount = self.value

        if self.max_discount_amount is not None:
            discount = min(discount, self.max_discount_amount)

        # Percentage maths yields 4dp (100.00 * 0.10 == 10.0000); this is a
        # currency amount and everything downstream -- the redemption row, the
        # order total, the API string -- is 2dp.
        return min(discount, order_subtotal).quantize(Decimal("0.01"))

    def validate_for(self, *, user, order_subtotal: Decimal):
        """Raises ValidationError with a user-facing reason, or returns silently if valid."""
        from django.utils import timezone

        now = timezone.now()
        if not self.is_active:
            raise ValidationError("This coupon is no longer active.")
        if now < self.valid_from or now > self.valid_until:
            raise ValidationError("This coupon is not valid at this time.")
        if order_subtotal < self.min_order_amount:
            raise ValidationError(
                f"This coupon requires a minimum order of {self.min_order_amount}."
            )
        if self.usage_limit is not None and self.times_used >= self.usage_limit:
            raise ValidationError("This coupon has reached its usage limit.")
        if user is not None and user.is_authenticated:
            user_redemptions = CouponRedemption.objects.filter(coupon=self, user=user).count()
            if user_redemptions >= self.per_user_limit:
                raise ValidationError("You have already used this coupon the maximum number of times.")


class CouponRedemption(models.Model):
    """One row per successful use — lets per-user limits be enforced without mutating
    a counter on the User model, and gives an audit trail of who used what, when."""

    coupon = models.ForeignKey(Coupon, on_delete=models.CASCADE, related_name="redemptions")
    user = models.ForeignKey(
        "users.User", on_delete=models.SET_NULL, null=True, related_name="coupon_redemptions",
    )
    order = models.OneToOneField(
        "app.Order", on_delete=models.CASCADE, related_name="coupon_redemption",
    )
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.coupon.code} redeemed on order {self.order_id}"
