from datetime import timedelta
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import models

RETURN_WINDOW_DAYS = 14


class ReturnRequest(models.Model):
    STATUS_REQUESTED = "requested"
    STATUS_APPROVED = "approved"
    STATUS_REJECTED = "rejected"
    STATUS_REFUNDED = "refunded"

    STATUS_CHOICES = [
        (STATUS_REQUESTED, "Requested"),
        (STATUS_APPROVED, "Approved"),
        (STATUS_REJECTED, "Rejected"),
        (STATUS_REFUNDED, "Refunded"),
    ]

    # Its own small state machine — separate from Order's, since a return can be
    # rejected without ever touching the parent order's status.
    VALID_TRANSITIONS = {
        STATUS_REQUESTED: {STATUS_APPROVED, STATUS_REJECTED},
        STATUS_APPROVED: {STATUS_REFUNDED},
        STATUS_REJECTED: set(),
        STATUS_REFUNDED: set(),
    }

    order = models.ForeignKey("app.Order", on_delete=models.CASCADE, related_name="return_requests")
    reason = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_REQUESTED)
    refund_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    staff_notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Return for order {self.order_id} ({self.status})"

    @staticmethod
    def is_within_return_window(order) -> bool:
        """An order can only be returned within RETURN_WINDOW_DAYS of delivery —
        enforced here, by date, rather than left to staff judgment (per the
        directive's 'clear return-window policy enforced by dates' requirement)."""
        if order.delivered_at is None:
            return False
        from django.utils import timezone
        return timezone.now() <= order.delivered_at + timedelta(days=RETURN_WINDOW_DAYS)

    def clean(self):
        if self._state.adding:
            if self.order.status not in {self.order.STATUS_DELIVERED, self.order.STATUS_COMPLETED}:
                raise ValidationError("Only delivered or completed orders can be returned.")
            if not self.is_within_return_window(self.order):
                raise ValidationError(
                    f"The {RETURN_WINDOW_DAYS}-day return window for this order has closed."
                )

    def transition_to(self, new_status: str) -> None:
        allowed = self.VALID_TRANSITIONS.get(self.status, set())
        if new_status not in allowed:
            raise ValueError(
                f"Cannot move return request {self.id} from '{self.status}' to '{new_status}'."
            )

        if new_status == self.STATUS_REFUNDED:
            # Refunding is the one return outcome that has to reach Paystack --
            # do that first, and only update local status once it actually
            # succeeds, so a rejected/failed refund never gets recorded as if
            # money moved. See app.services.refund_order_payment.
            from app.services import refund_order_payment

            try:
                refund_order_payment(self.order, amount=self.refund_amount)
            except Exception as exc:
                raise ValueError(f"Refund failed for return request {self.id}: {exc}") from exc

        self.status = new_status
        self.save(update_fields=["status", "updated_at"])

        if new_status == self.STATUS_APPROVED and self.order.status != self.order.STATUS_RETURNED:
            self.order.transition_to(self.order.STATUS_RETURNED)
