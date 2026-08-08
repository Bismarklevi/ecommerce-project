"""Paystack client — the dominant Ghanaian payment processor, covering cards and
Mobile Money (MTN MoMo, Vodafone Cash, AirtelTigo) through one Charge/Initialize API.

Kept as a thin wrapper so payments.py service logic and views never import `requests`
or know about Paystack's specific JSON shape directly.
"""
import hashlib
import hmac
import uuid

import requests
from django.conf import settings


class PaystackError(Exception):
    pass


def _headers():
    if not settings.PAYSTACK_SECRET_KEY:
        raise PaystackError(
            "PAYSTACK_SECRET_KEY is not configured. Set it in the environment before "
            "initiating live payments."
        )
    return {
        "Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}",
        "Content-Type": "application/json",
    }


def generate_reference() -> str:
    return f"kaira_{uuid.uuid4().hex[:20]}"


def initialize_transaction(*, email: str, amount_pesewas: int, reference: str, callback_url: str = "") -> dict:
    """Amount must be in the smallest currency unit (pesewas for GHS), per Paystack's
    API contract — passing cedis directly is a classic 100x overcharge bug."""
    payload = {
        "email": email,
        "amount": amount_pesewas,
        "reference": reference,
        "currency": "GHS",
    }
    if callback_url:
        payload["callback_url"] = callback_url

    try:
        response = requests.post(
            f"{settings.PAYSTACK_BASE_URL}/transaction/initialize",
            json=payload,
            headers=_headers(),
            timeout=15,
        )
    except requests.RequestException as exc:
        raise PaystackError(f"Could not reach Paystack: {exc}") from exc

    try:
        data = response.json()
    except ValueError as exc:
        # Paystack is down/unreachable in a way that returns something that
        # isn't JSON at all (an HTML error page, a proxy block, etc). Turn
        # this into the same PaystackError callers already handle instead of
        # letting a raw JSONDecodeError become an unhandled 500.
        raise PaystackError(
            f"Paystack returned an unexpected response (status {response.status_code})."
        ) from exc

    if not response.ok or not data.get("status"):
        raise PaystackError(data.get("message", "Paystack initialization failed."))
    return data["data"]  # contains authorization_url, access_code, reference


def verify_transaction(reference: str) -> dict:
    try:
        response = requests.get(
            f"{settings.PAYSTACK_BASE_URL}/transaction/verify/{reference}",
            headers=_headers(),
            timeout=15,
        )
    except requests.RequestException as exc:
        raise PaystackError(f"Could not reach Paystack: {exc}") from exc

    try:
        data = response.json()
    except ValueError as exc:
        raise PaystackError(
            f"Paystack returned an unexpected response (status {response.status_code})."
        ) from exc

    if not response.ok or not data.get("status"):
        raise PaystackError(data.get("message", "Paystack verification failed."))
    return data["data"]  # contains status ("success"/"failed"), amount, gateway_response


def verify_webhook_signature(raw_body: bytes, signature_header: str) -> bool:
    """Paystack signs webhook bodies with HMAC-SHA512 of the raw request body using
    the secret key. Comparing with hmac.compare_digest to avoid timing attacks —
    a plain `==` check here would be the kind of subtle vulnerability that passes
    every functional test and fails only under real attack."""
    if not settings.PAYSTACK_SECRET_KEY or not signature_header:
        return False
    computed = hmac.new(
        settings.PAYSTACK_SECRET_KEY.encode("utf-8"), raw_body, hashlib.sha512
    ).hexdigest()
    return hmac.compare_digest(computed, signature_header)


def create_refund(*, reference: str, amount_pesewas: int | None = None) -> dict:
    """Refunds a previously-successful transaction. Omitting `amount_pesewas`
    refunds the full original amount (Paystack's own default); passing it
    allows a partial refund. Like initialize/verify, this only ever talks to
    Paystack -- it never touches Payment/Order state itself, so the caller
    (app.services.refund_order_payment) stays the single place that decides
    what a successful refund means for the rest of the system."""
    payload = {"transaction": reference}
    if amount_pesewas is not None:
        payload["amount"] = amount_pesewas

    try:
        response = requests.post(
            f"{settings.PAYSTACK_BASE_URL}/refund",
            json=payload,
            headers=_headers(),
            timeout=15,
        )
    except requests.RequestException as exc:
        raise PaystackError(f"Could not reach Paystack: {exc}") from exc

    try:
        data = response.json()
    except ValueError as exc:
        raise PaystackError(
            f"Paystack returned an unexpected response (status {response.status_code})."
        ) from exc

    if not response.ok or not data.get("status"):
        raise PaystackError(data.get("message", "Paystack refund failed."))
    return data["data"]
