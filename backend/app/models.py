from decimal import Decimal

from django.conf import settings
from django.db import models
from django.dispatch import Signal

from products.models import ProductVariant

# Dispatched by Order.transition_to(). Receivers get (sender=Order, order, previous_status, new_status).
# Kept here rather than in a shared signals.py to avoid a circular import between
# app.models and the notifications app.
order_status_changed = Signal()


class Cart(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="cart",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]

    @property
    def item_count(self):
        return sum(item.quantity for item in self.items.all())

    @property
    def subtotal(self):
        total = Decimal("0.00")
        for item in self.items.all():
            total += item.line_total
        return total

    def __str__(self):
        return f"Cart for {self.user.username}"


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name="items")
    product_variant = models.ForeignKey(
        ProductVariant,
        on_delete=models.CASCADE,
        related_name="cart_items",
    )
    quantity = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("cart", "product_variant")
        ordering = ["id"]

    @property
    def unit_price(self):
        return self.product_variant.effective_price

    @property
    def line_total(self):
        return self.unit_price * self.quantity

    def __str__(self):
        return f"{self.cart.user.username} - {self.product_variant}"


class Order(models.Model):
    STATUS_PENDING = "pending"
    STATUS_PAID = "paid"
    STATUS_PROCESSING = "processing"
    STATUS_SHIPPED = "shipped"
    STATUS_DELIVERED = "delivered"
    STATUS_COMPLETED = "completed"
    STATUS_CANCELLED = "cancelled"
    STATUS_RETURNED = "returned"

    PAYMENT_UNPAID = "unpaid"
    PAYMENT_PENDING = "pending"
    PAYMENT_PAID = "paid"
    PAYMENT_FAILED = "failed"
    PAYMENT_REFUNDED = "refunded"

    STATUS_CHOICES = [
        (STATUS_PENDING, "Pending"),
        (STATUS_PAID, "Paid"),
        (STATUS_PROCESSING, "Processing"),
        (STATUS_SHIPPED, "Shipped"),
        (STATUS_DELIVERED, "Delivered"),
        (STATUS_COMPLETED, "Completed"),
        (STATUS_CANCELLED, "Cancelled"),
        (STATUS_RETURNED, "Returned"),
    ]
    PAYMENT_STATUS_CHOICES = [
        (PAYMENT_UNPAID, "Unpaid"),
        (PAYMENT_PENDING, "Pending"),
        (PAYMENT_PAID, "Paid"),
        (PAYMENT_FAILED, "Failed"),
        (PAYMENT_REFUNDED, "Refunded"),
    ]

    # The state machine itself: maps each status to the set of statuses it may move to.
    # Nothing outside Order.transition_to() should ever write to `status` directly —
    # not the admin, not a view, not a management command — so this is the single
    # source of truth for "is this transition allowed."
    VALID_TRANSITIONS = {
        STATUS_PENDING: {STATUS_PAID, STATUS_CANCELLED},
        STATUS_PAID: {STATUS_PROCESSING, STATUS_CANCELLED},
        STATUS_PROCESSING: {STATUS_SHIPPED, STATUS_CANCELLED},
        STATUS_SHIPPED: {STATUS_DELIVERED, STATUS_RETURNED},
        STATUS_DELIVERED: {STATUS_COMPLETED, STATUS_RETURNED},
        STATUS_COMPLETED: {STATUS_RETURNED},
        STATUS_CANCELLED: set(),
        STATUS_RETURNED: set(),
    }

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="orders",
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    payment_status = models.CharField(
        max_length=20,
        choices=PAYMENT_STATUS_CHOICES,
        default=PAYMENT_UNPAID,
    )
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    shipping_zone = models.ForeignKey(
        "shipping.ShippingZone", on_delete=models.PROTECT, null=True, blank=True, related_name="orders",
    )
    shipping_cost = models.DecimalField(max_digits=8, decimal_places=2, default=Decimal("0.00"))
    tracking_number = models.CharField(max_length=80, blank=True)
    shipping_name = models.CharField(max_length=255, blank=True)
    shipping_email = models.EmailField(blank=True)
    shipping_phone = models.CharField(max_length=32, blank=True)
    shipping_address = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    delivered_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    @property
    def item_count(self):
        return sum(item.quantity for item in self.items.all())

    def transition_to(self, new_status: str, *, save: bool = True) -> None:
        """The only sanctioned way to change an order's status. Raises ValueError on
        any transition not present in VALID_TRANSITIONS — this is what makes the
        state machine real rather than advisory."""
        allowed = self.VALID_TRANSITIONS.get(self.status, set())
        if new_status not in allowed:
            raise ValueError(
                f"Cannot transition order {self.id} from '{self.status}' to '{new_status}'. "
                f"Allowed next states: {sorted(allowed) or 'none (terminal state)'}."
            )
        previous_status = self.status
        self.status = new_status
        update_fields = ["status", "updated_at"]

        if new_status == self.STATUS_DELIVERED and self.delivered_at is None:
            from django.utils import timezone
            self.delivered_at = timezone.now()
            update_fields.append("delivered_at")

        if save:
            self.save(update_fields=update_fields)

        # Decoupled event dispatch: notifications (and anything else) subscribes to
        # this signal rather than being called directly from here, so the order
        # model has zero import-time dependency on the notifications app.
        order_status_changed.send(
            sender=self.__class__, order=self, previous_status=previous_status, new_status=new_status,
        )

    def __str__(self):
        return f"Order {self.id} for {self.user.username}"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product_variant = models.ForeignKey(ProductVariant, on_delete=models.PROTECT)
    product_name = models.CharField(max_length=180)
    product_sku = models.CharField(max_length=80)
    size = models.CharField(max_length=20)
    color = models.CharField(max_length=50)
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    line_total = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["id"]

    def save(self, *args, **kwargs):
        self.line_total = self.unit_price * self.quantity
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Order {self.order.id} - {self.product_name}"


class Payment(models.Model):
    STATUS_PENDING = "pending"
    STATUS_SUCCESS = "success"
    STATUS_FAILED = "failed"
    STATUS_REFUNDED = "refunded"
    # A Paystack-verified charge.success whose amount or currency doesn't
    # match what this order expected. Never auto-resolved -- see
    # PaystackWebhookView. Distinct from FAILED (a routine declined card)
    # because this means Paystack confirms money moved, just not the right
    # amount, which needs a human to look at, not a "customer can just retry".
    STATUS_FLAGGED = "flagged"

    STATUS_CHOICES = [
        (STATUS_PENDING, "Pending"),
        (STATUS_SUCCESS, "Success"),
        (STATUS_FAILED, "Failed"),
        (STATUS_REFUNDED, "Refunded"),
        (STATUS_FLAGGED, "Flagged — needs review"),
    ]

    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name="payment")
    provider = models.CharField(max_length=50, default="paystack")
    reference = models.CharField(max_length=120, unique=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    raw_response = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Payment for order {self.order_id} - {self.status}"

