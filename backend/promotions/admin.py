from django.contrib import admin

from .models import Coupon, CouponRedemption


class CouponRedemptionInline(admin.TabularInline):
    model = CouponRedemption
    extra = 0
    readonly_fields = ("user", "order", "discount_amount", "created_at")
    can_delete = False


@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = (
        "code", "discount_type", "value", "times_used", "usage_limit",
        "is_active", "valid_from", "valid_until",
    )
    list_filter = ("discount_type", "is_active")
    search_fields = ("code",)
    readonly_fields = ("times_used",)
    inlines = [CouponRedemptionInline]
