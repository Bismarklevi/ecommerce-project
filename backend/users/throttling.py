"""Rate-limiting for the abuse-prone auth endpoints.

Why not the stock IP-based throttles: the Next.js frontend proxies auth calls
server-side, so every login/register reaches Django from the *proxy's* IP. An
IP-keyed throttle would therefore rate-limit the entire storefront collectively
(and, conversely, an attacker rotating source IPs would sail past one). Keying on
the submitted account identifier limits credential-stuffing against a single
account no matter where the traffic comes from. Registration -- where there is no
existing account to key on -- stays IP-scoped, and the proxy forwards
X-Forwarded-For so that key is the real client where a trusted proxy is in front.
"""

from rest_framework.throttling import AnonRateThrottle, SimpleRateThrottle


class _IdentifierRateThrottle(SimpleRateThrottle):
    """Throttle keyed on a request-body identifier (email/username), falling back
    to the client IP when the body carries neither (e.g. password-reset confirm,
    which only has a token)."""

    identifier_fields = ("email", "username")

    def get_cache_key(self, request, view):
        ident = ""
        data = getattr(request, "data", None) or {}
        for field in self.identifier_fields:
            value = data.get(field)
            if value:
                ident = str(value).strip().lower()
                break
        if not ident:
            ident = self.get_ident(request)  # falls back to (forwarded) client IP
        return self.cache_format % {"scope": self.scope, "ident": ident}


class LoginRateThrottle(_IdentifierRateThrottle):
    scope = "login"


class PasswordResetRateThrottle(_IdentifierRateThrottle):
    scope = "password_reset"


class RegisterRateThrottle(AnonRateThrottle):
    """Registration abuse is about mass account creation from one source, so this
    one is intentionally IP-scoped (see module docstring re: X-Forwarded-For)."""

    scope = "register"
