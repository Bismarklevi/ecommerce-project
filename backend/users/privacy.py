"""Data-subject rights: export and erasure.

Implements the right of access and the right to erasure required by GDPR and
Ghana's Data Protection Act, 2012 (Act 843). Erasure is balanced against legal
retention: order and payment records carry tax/accounting obligations, so they
are kept but scrubbed of identifying information rather than deleted outright.
"""

import uuid

from django.db import transaction
from rest_framework.authtoken.models import Token


def build_personal_data_export(user) -> dict:
    """Return everything personal we hold about `user` as JSON-serializable data."""
    return {
        "account": {
            "username": user.username,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "phone_number": user.phone_number,
            "default_shipping_address": user.default_shipping_address,
            "date_joined": user.date_joined.isoformat() if user.date_joined else None,
            "last_login": user.last_login.isoformat() if user.last_login else None,
        },
        "addresses": [
            {
                "label": a.label,
                "full_name": a.full_name,
                "phone_number": a.phone_number,
                "address_line1": a.address_line1,
                "address_line2": a.address_line2,
                "city": a.city,
                "region": a.region,
                "country": a.country,
                "is_default": a.is_default,
            }
            for a in user.addresses.all()
        ],
        "orders": [
            {
                "id": o.id,
                "status": o.status,
                "payment_status": o.payment_status,
                "total_amount": str(o.total_amount),
                "created_at": o.created_at.isoformat(),
                "shipping_name": o.shipping_name,
                "shipping_email": o.shipping_email,
                "shipping_phone": o.shipping_phone,
                "shipping_address": o.shipping_address,
                "items": [
                    {
                        "product_name": i.product_name,
                        "size": i.size,
                        "color": i.color,
                        "quantity": i.quantity,
                        "unit_price": str(i.unit_price),
                        "line_total": str(i.line_total),
                    }
                    for i in o.items.all()
                ],
            }
            for o in user.orders.prefetch_related("items")
        ],
        "reviews": [
            {
                "product": r.product.name,
                "rating": r.rating,
                "title": r.title,
                "body": r.body,
                "created_at": r.created_at.isoformat(),
            }
            for r in user.reviews.select_related("product")
        ],
        "wishlist": [
            {"product": w.product.name, "added_at": w.created_at.isoformat()}
            for w in user.wishlist_items.select_related("product")
        ],
    }


@transaction.atomic
def anonymize_user(user) -> None:
    """Erase the user's personal data. Records with a legal retention obligation
    (orders, their line items, and payments) are kept but stripped of identifying
    details; everything else personal is deleted and the account is locked."""
    suffix = uuid.uuid4().hex[:12]

    # Scrub the PII snapshots frozen onto retained orders at checkout time.
    user.orders.update(
        shipping_name="[deleted]",
        shipping_email="",
        shipping_phone="",
        shipping_address="[deleted]",
    )

    # Delete data we have no obligation to retain.
    user.addresses.all().delete()
    user.reviews.all().delete()
    user.wishlist_items.all().delete()
    if hasattr(user, "cart"):
        user.cart.delete()
    Token.objects.filter(user=user).delete()

    # Scrub and lock the account itself. The row is kept (orders still reference
    # it) but no longer identifies a real person and can never be logged into.
    user.username = f"deleted_{suffix}"
    user.email = f"deleted_{suffix}@deleted.invalid"
    user.first_name = ""
    user.last_name = ""
    user.phone_number = ""
    user.default_shipping_address = ""
    user.is_active = False
    user.set_unusable_password()
    user.save()
