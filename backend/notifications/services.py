"""Event -> notification dispatch.

`send()` writes an audit row (Notification) and, for the email channel,
actually delivers it through Django's configured EMAIL_BACKEND -- console in
dev, real SMTP/Resend/SendGrid once EMAIL_* env vars are set (see
project/settings.py). Every call site in this codebase goes through
`notify()`, never a mail library directly, so the delivery mechanism stays a
one-function swap.
"""
import logging

from django.conf import settings

from users.mail import PlainAsciiEmailMessage

from .models import Notification

logger = logging.getLogger("notifications")

ORDER_STATUS_MESSAGES = {
    "paid": "Your order #{order_id} has been paid — we're getting it ready.",
    "processing": "Your order #{order_id} is being prepared for shipment.",
    "shipped": "Your order #{order_id} is on its way! Tracking: {tracking_number}",
    "delivered": "Your order #{order_id} has been delivered. Enjoy!",
    "cancelled": "Your order #{order_id} has been cancelled.",
    "returned": "Your return for order #{order_id} has been processed.",
}


def _send(notification: Notification) -> None:
    """Console backend in dev, real email in any environment with EMAIL_HOST
    configured -- either way it goes through the same Django mail API, so
    nothing here needs to know which one it currently is."""
    from django.utils import timezone

    logger.info(
        "NOTIFY[%s] to user=%s subject=%r body=%r",
        notification.channel, notification.user_id, notification.subject, notification.body,
    )

    if notification.channel == Notification.CHANNEL_EMAIL:
        recipient = notification.user.email if notification.user_id else None
        if not recipient:
            raise ValueError(f"Notification {notification.id} has no recipient email address.")
        PlainAsciiEmailMessage(
            subject=notification.subject,
            body=notification.body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[recipient],
        ).send(fail_silently=False)
    # SMS/in-app channels aren't wired to a real provider yet -- the audit row
    # above is still written, this just doesn't attempt delivery for them.

    notification.status = Notification.STATUS_SENT
    notification.sent_at = timezone.now()
    notification.save(update_fields=["status", "sent_at"])


def notify(*, user, event_type: str, subject: str = "", body: str = "", channel: str = Notification.CHANNEL_EMAIL) -> Notification:
    notification = Notification.objects.create(
        user=user, event_type=event_type, channel=channel, subject=subject, body=body,
    )
    try:
        _send(notification)
    except Exception:  # pragma: no cover - defensive: a notify failure must never break checkout/fulfillment
        logger.exception("Failed to send notification id=%s", notification.id)
        notification.status = Notification.STATUS_FAILED
        notification.save(update_fields=["status"])
    return notification


def notify_order_status_change(order, new_status: str) -> None:
    template = ORDER_STATUS_MESSAGES.get(new_status)
    if not template:
        return
    body = template.format(order_id=order.id, tracking_number=order.tracking_number or "pending")
    notify(
        user=order.user,
        event_type=f"order.{new_status}",
        subject=f"Kaira order #{order.id} update",
        body=body,
    )
