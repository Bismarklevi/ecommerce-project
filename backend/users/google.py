"""Google sign-in: verify the ID token the browser got from Google Identity
Services, then map it onto a local User.

The frontend never talks to our API with a Google access token -- it hands us
the signed ID token (a JWT) and we verify its signature and audience here with
Google's published keys. Nothing is trusted from the request body itself."""

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.utils.text import slugify
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token

User = get_user_model()

_GOOGLE_ISSUERS = {"accounts.google.com", "https://accounts.google.com"}


class GoogleAuthError(Exception):
    """The credential could not be verified (bad signature, wrong audience,
    expired, unverified email). Maps to 401."""


class GoogleNotConfigured(GoogleAuthError):
    """GOOGLE_CLIENT_ID is unset, so no token can be verified. Maps to 503:
    a deployment problem, not a bad request."""


def verify_google_credential(credential: str) -> dict:
    """Return the verified claims we care about, or raise GoogleAuthError."""
    if not settings.GOOGLE_CLIENT_ID:
        raise GoogleNotConfigured("Google sign-in is not configured on this server.")
    try:
        claims = id_token.verify_oauth2_token(
            credential, google_requests.Request(), settings.GOOGLE_CLIENT_ID
        )
    except ValueError as exc:
        # google-auth raises ValueError for every verification failure: bad
        # signature, expired, audience mismatch. All of them are "not you".
        raise GoogleAuthError("Google sign-in could not be verified.") from exc

    if claims.get("iss") not in _GOOGLE_ISSUERS:
        raise GoogleAuthError("Google sign-in could not be verified.")
    # An unverified address must not be allowed to claim an existing account
    # by email -- that's the whole basis of the link-by-email below.
    if not claims.get("email_verified") or not claims.get("email"):
        raise GoogleAuthError("Your Google account email is not verified.")

    return {
        "email": claims["email"],
        "given_name": claims.get("given_name", ""),
        "family_name": claims.get("family_name", ""),
        "sub": claims["sub"],
    }


def _unique_username(base: str) -> str:
    base = slugify(base).replace("-", "") or "user"
    base = base[:140]
    candidate = base
    n = 1
    while User.objects.filter(username__iexact=candidate).exists():
        n += 1
        candidate = f"{base}{n}"
    return candidate


def get_or_create_user_for_google(info: dict):
    """Find the user by verified email, or create one. Returns (user, created).

    Linking by email is safe only because verify_google_credential refused any
    token whose email Google hasn't verified. A created user gets an unusable
    password: they sign in with Google, and "forgot password" is how they'd
    set one if they ever want a password too."""
    email = info["email"]
    user = User.objects.filter(email__iexact=email).first()
    if user is not None:
        return user, False

    with transaction.atomic():
        user = User(
            username=_unique_username(email.split("@", 1)[0]),
            email=email,
            first_name=info.get("given_name", "")[:150],
            last_name=info.get("family_name", "")[:150],
        )
        user.set_unusable_password()
        try:
            user.save()
        except IntegrityError:
            # Lost a race with a concurrent first sign-in on the same email.
            user = User.objects.get(email__iexact=email)
            return user, False
    return user, True
