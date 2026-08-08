import sys
from pathlib import Path


from decouple import AutoConfig, Csv

BASE_DIR = Path(__file__).resolve().parent.parent
config = AutoConfig(search_path=str(BASE_DIR))


def as_bool(value):
    return str(value).strip().lower() in {"1", "true", "yes", "on"}

SECRET_KEY = config("SECRET_KEY", default="django-insecure-change-me")
DEBUG = config("DEBUG", default=False, cast=as_bool)

# Fail fast rather than boot a public deployment with the throwaway dev key.
if not DEBUG and SECRET_KEY == "django-insecure-change-me" and "test" not in sys.argv:
    raise RuntimeError(
        "SECRET_KEY is still the insecure development default while DEBUG=False. "
        "Set a real SECRET_KEY in the environment before deploying."
    )

ALLOWED_HOSTS = config(
    "ALLOWED_HOSTS",
    default="localhost,127.0.0.1,0.0.0.0",
    cast=Csv(),
)

INSTALLED_APPS = [
    "unfold",
    "unfold.contrib.filters",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "corsheaders",
    "rest_framework",
    "rest_framework.authtoken",
    "django_filters",
    "drf_spectacular",
    "users",
    "products",
    "app",
    "wishlist",
    "promotions",
    "shipping",
    "returns",
    "notifications",
    "cms",
    "analytics",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "project.urls"
WSGI_APPLICATION = "project.wsgi.application"
ASGI_APPLICATION = "project.asgi.application"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "project" / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

DATABASE_ENGINE = config("DATABASE_ENGINE", default="django.db.backends.postgresql")
DATABASE_NAME = config("DATABASE_NAME", default="ecommerce")

DATABASES = {
    "default": {
        "ENGINE": DATABASE_ENGINE,
        "NAME": DATABASE_NAME,
        "USER": config("DATABASE_USER", default="postgres"),
        "PASSWORD": config("DATABASE_PASSWORD", default=""),
        "HOST": config("DATABASE_HOST", default="127.0.0.1"),
        "PORT": config("DATABASE_PORT", default="5432"),
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

USE_CLOUDFLARE_R2 = as_bool(config("USE_CLOUDFLARE_R2", default=False))
CLOUDFLARE_R2_BUCKET_NAME = config("CLOUDFLARE_R2_BUCKET_NAME", default="")
CLOUDFLARE_R2_ENDPOINT_URL = config("CLOUDFLARE_R2_ENDPOINT_URL", default="")
CLOUDFLARE_R2_ACCESS_KEY_ID = config("CLOUDFLARE_R2_ACCESS_KEY_ID", default="")
CLOUDFLARE_R2_SECRET_ACCESS_KEY = config("CLOUDFLARE_R2_SECRET_ACCESS_KEY", default="")
CLOUDFLARE_R2_REGION_NAME = config("CLOUDFLARE_R2_REGION_NAME", default="auto")
CLOUDFLARE_R2_CUSTOM_DOMAIN = config("CLOUDFLARE_R2_CUSTOM_DOMAIN", default="")
CLOUDFLARE_R2_LOCATION = config("CLOUDFLARE_R2_LOCATION", default="media")

if USE_CLOUDFLARE_R2:
    MEDIA_URL = (
        f"https://{CLOUDFLARE_R2_CUSTOM_DOMAIN.rstrip('/')}/media/"
        if CLOUDFLARE_R2_CUSTOM_DOMAIN
        else MEDIA_URL
    )

    STORAGES = {
        "default": {
            "BACKEND": "storages.backends.s3boto3.S3Boto3Storage",
            "OPTIONS": {
                "access_key": CLOUDFLARE_R2_ACCESS_KEY_ID,
                "secret_key": CLOUDFLARE_R2_SECRET_ACCESS_KEY,
                "bucket_name": CLOUDFLARE_R2_BUCKET_NAME,
                "endpoint_url": CLOUDFLARE_R2_ENDPOINT_URL,
                "region_name": CLOUDFLARE_R2_REGION_NAME,
                "custom_domain": CLOUDFLARE_R2_CUSTOM_DOMAIN or None,
                "location": CLOUDFLARE_R2_LOCATION,
                "default_acl": None,
                "file_overwrite": False,
                "querystring_auth": False,
                "addressing_style": "path",
                "signature_version": "s3v4",
            },
        },
        "staticfiles": {
            "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
        },
    }
else:
    STORAGES = {
        "default": {
            "BACKEND": "django.core.files.storage.FileSystemStorage",
            "OPTIONS": {
                "location": MEDIA_ROOT,
                "base_url": MEDIA_URL,
            },
        },
        "staticfiles": {
            "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
        },
    }

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
AUTH_USER_MODEL = "users.User"

CORS_ALLOWED_ORIGINS = config(
    "CORS_ALLOWED_ORIGINS",
    default="http://localhost:3000,http://127.0.0.1:3000",
    cast=Csv(),
)
CORS_ALLOW_CREDENTIALS = True
CSRF_TRUSTED_ORIGINS = config(
    "CSRF_TRUSTED_ORIGINS",
    default="http://localhost:3000,http://127.0.0.1:3000",
    cast=Csv(),
)

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        # TokenAuthentication is what the Next.js frontend uses: it stores the
        # opaque token in an httpOnly cookie and only ever attaches it as an
        # Authorization header from server-side code (route handlers, server
        # components) -- browser JS never touches it, which is the same
        # "no stealable credential in reach of a script" property session auth
        # is chosen for elsewhere in this file. SessionAuthentication stays
        # enabled for the Django admin and the browsable API.
        "rest_framework.authentication.TokenAuthentication",
        "rest_framework.authentication.SessionAuthentication",
        "rest_framework.authentication.BasicAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.AllowAny",
    ],
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_PAGINATION_CLASS": "project.pagination.StandardResultsPagination",
    "PAGE_SIZE": 100,
    # Deliberately no DEFAULT_THROTTLE_CLASSES: a global throttle would be keyed
    # on the proxy's IP (the Next.js frontend fetches the catalog server-side)
    # and so would rate-limit all shoppers as one. Throttling is applied per-view
    # to the abuse-prone auth/payment endpoints instead -- see users.throttling.
    "DEFAULT_THROTTLE_RATES": {
        "login": "10/min",
        "register": "20/hour",
        "password_reset": "5/hour",
        "payment": "30/min",
    },
}

# Throttling shares the cache across the whole process, so during the test run
# accumulated auth requests would trip these limits and fail unrelated tests.
# Disabling the rates (None => allow) keeps the suite deterministic; production
# and dev are unaffected.
if "test" in sys.argv:
    REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"] = {
        scope: None for scope in REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"]
    }

SPECTACULAR_SETTINGS = {
    "TITLE": "Kaira Ghana E-Commerce API",
    "DESCRIPTION": (
        "REST API for the Kaira clothing storefront: catalog, cart, checkout, "
        "payments (Paystack + Mobile Money), wishlist, and promotions."
    ),
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
    "SCHEMA_PATH_PREFIX": "/api/",
    "TAGS": [
        {"name": "Auth", "description": "Registration, session/login, current user"},
        {"name": "Catalog", "description": "Categories, products, variants, reviews"},
        {"name": "Cart", "description": "Guest/authenticated cart management"},
        {"name": "Orders", "description": "Order lifecycle and checkout"},
        {"name": "Payments", "description": "Paystack + Mobile Money payment processing"},
        {"name": "Wishlist", "description": "Saved-for-later products"},
        {"name": "Promotions", "description": "Coupons and discount codes"},
    ],
}

# Paystack — dominant Ghanaian payment processor (cards + Mobile Money via Paystack Charge API)
PAYSTACK_SECRET_KEY = config("PAYSTACK_SECRET_KEY", default="")
PAYSTACK_PUBLIC_KEY = config("PAYSTACK_PUBLIC_KEY", default="")
PAYSTACK_BASE_URL = "https://api.paystack.co"

# Used to build the Paystack callback_url (where the customer lands after paying)
# and nowhere else -- keeping the redirect target server-side avoids trusting a
# client-supplied URL.
FRONTEND_URL = config("FRONTEND_URL", default="http://localhost:3000").rstrip("/")

# Email — defaults to printing to the console so password-reset/order emails are
# visible in local dev without any setup. Set EMAIL_BACKEND to Django's SMTP
# backend (and the EMAIL_HOST_* vars) to send real mail through Resend/SendGrid/
# any SMTP provider in staging or production.
EMAIL_BACKEND = config("EMAIL_BACKEND", default="django.core.mail.backends.console.EmailBackend")
EMAIL_HOST = config("EMAIL_HOST", default="")
EMAIL_PORT = config("EMAIL_PORT", default=587, cast=int)
EMAIL_HOST_USER = config("EMAIL_HOST_USER", default="")
EMAIL_HOST_PASSWORD = config("EMAIL_HOST_PASSWORD", default="")
EMAIL_USE_TLS = config("EMAIL_USE_TLS", default=True, cast=as_bool)
DEFAULT_FROM_EMAIL = config("DEFAULT_FROM_EMAIL", default="Kaira <no-reply@kaira.example.com>")

# Free-tier API keys used only by the `seed_womens_catalog` / `seed_homepage_banners`
# management commands to pull real photography for category tiles, product images,
# and homepage banners. Safe to leave blank in any environment that doesn't need to
# (re)run those seed commands. See backend/app/stock_photos.py for how to obtain them.
UNSPLASH_ACCESS_KEY = config("UNSPLASH_ACCESS_KEY", default="")
PEXELS_API_KEY = config("PEXELS_API_KEY", default="")

# ─────────────────────────── Security headers ───────────────────────────
# Always-on hardening (cheap, no HTTPS assumption):
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "same-origin"
X_FRAME_OPTIONS = "DENY"

# HTTPS-dependent hardening -- only switched on when DEBUG is off, so local dev
# over http keeps working. Each is overridable via env for hosts that terminate
# TLS differently. SECURE_PROXY_SSL_HEADER tells Django to trust the standard
# X-Forwarded-Proto set by the platform's load balancer / the Next.js proxy.
if not DEBUG:
    SECURE_SSL_REDIRECT = config("SECURE_SSL_REDIRECT", default=True, cast=as_bool)
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    SECURE_HSTS_SECONDS = config("SECURE_HSTS_SECONDS", default=31536000, cast=int)
    SECURE_HSTS_INCLUDE_SUBDOMAINS = config("SECURE_HSTS_INCLUDE_SUBDOMAINS", default=True, cast=as_bool)
    SECURE_HSTS_PRELOAD = config("SECURE_HSTS_PRELOAD", default=True, cast=as_bool)
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True

UNFOLD = {
    "SITE_TITLE": "Kaira Admin",
    "SITE_HEADER": "Kaira Ghana E-Commerce",
    "SITE_SYMBOL": "storefront",
    "SHOW_HISTORY": True,
    "DASHBOARD_CALLBACK": "project.dashboard.dashboard_callback",
    "SIDEBAR": {
        "show_search": True,
        # False: show ONLY the curated business navigation below, not
        # Django's auto-generated "every registered model" app list as
        # well -- Phase 11 is explicit that the admin shouldn't feel like
        # "here are all my database tables".
        "show_all_applications": False,
        "navigation": "project.navigation.get_navigation",
    },
    "COLORS": {
        "primary": {
            "50": "253 246 240", "100": "250 232 214", "200": "244 205 163",
            "300": "237 173 108", "400": "224 138 62", "500": "204 106 31",
            "600": "178 79 20", "700": "148 61 18", "800": "112 46 20",
            "900": "84 35 18", "950": "46 19 10",
        },
    },
}
