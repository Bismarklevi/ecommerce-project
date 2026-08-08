from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView
from rest_framework.routers import DefaultRouter

from analytics.views import SalesReportView
from app.views import CartItemViewSet, CartViewSet, CheckoutView, OrderViewSet, PaymentViewSet, PaystackWebhookView
from cms.views import BannerViewSet, ContentBlockViewSet
from products.views import CategoryViewSet, ProductViewSet, ReviewViewSet
from promotions.views import CouponValidateView
from returns.views import ReturnRequestViewSet
from shipping.views import ShippingZoneViewSet
from users.views import (
    AddressViewSet,
    ChangePasswordView,
    CurrentUserView,
    LoginView,
    LogoutView,
    PasswordResetConfirmView,
    PasswordResetRequestView,
    RegisterView,
    UserViewSet,
)
from wishlist.views import WishlistViewSet

router = DefaultRouter()
router.register("users", UserViewSet, basename="user")
router.register("categories", CategoryViewSet, basename="category")
router.register("products", ProductViewSet, basename="product")
router.register("reviews", ReviewViewSet, basename="review")
router.register("cart", CartViewSet, basename="cart")
router.register("cart/items", CartItemViewSet, basename="cart-item")
router.register("orders", OrderViewSet, basename="order")
router.register("payments", PaymentViewSet, basename="payment")
router.register("wishlist", WishlistViewSet, basename="wishlist")
router.register("addresses", AddressViewSet, basename="address")
router.register("shipping-zones", ShippingZoneViewSet, basename="shipping-zone")
router.register("returns", ReturnRequestViewSet, basename="return-request")
router.register("banners", BannerViewSet, basename="banner")
router.register("content-blocks", ContentBlockViewSet, basename="content-block")

urlpatterns = [
    path("admin/", admin.site.urls),
    # These specific paths must be listed before the router include below --
    # DRF's default detail route is `api/<prefix>/<pk>/` with pk matching
    # almost any non-slash string, so `api/payments/webhook/` would otherwise
    # be swallowed by PaymentViewSet's detail route as pk="webhook" (a 401/404
    # from DRF, never reaching PaystackWebhookView at all). Confirmed by
    # `django.urls.resolve("/api/payments/webhook/")` before this fix -- it
    # returned PaymentViewSet, not PaystackWebhookView.
    path("api/me/", CurrentUserView.as_view(), name="current-user"),
    path("api/auth/register/", RegisterView.as_view(), name="auth-register"),
    path("api/auth/login/", LoginView.as_view(), name="auth-login"),
    path("api/auth/logout/", LogoutView.as_view(), name="auth-logout"),
    path("api/auth/password-reset/", PasswordResetRequestView.as_view(), name="password-reset-request"),
    path("api/auth/password-reset/confirm/", PasswordResetConfirmView.as_view(), name="password-reset-confirm"),
    path("api/account/change-password/", ChangePasswordView.as_view(), name="account-change-password"),
    path("api/orders/<int:order_id>/checkout/", CheckoutView.as_view(), name="order-checkout"),
    path("api/payments/webhook/", PaystackWebhookView.as_view(), name="paystack-webhook"),
    path("api/promotions/validate/", CouponValidateView.as_view(), name="coupon-validate"),
    path("api/analytics/sales/", SalesReportView.as_view(), name="sales-report"),
    # API documentation (Swagger/OpenAPI)
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("api/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
    # Router include LAST: its detail routes (`<prefix>/<pk>/`) are permissive
    # enough to shadow any single-segment literal path registered after it.
    path("api/", include(router.urls)),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

