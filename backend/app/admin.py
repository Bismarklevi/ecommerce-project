from django.contrib import admin
from unfold.admin import ModelAdmin, TabularInline

from .models import Cart, CartItem, Order, OrderItem, Payment


def _make_transition_action(target_status, label):
    def action(modeladmin, request, queryset):
        succeeded, failed = 0, []
        for order in queryset:
            try:
                order.transition_to(target_status)
                succeeded += 1
            except ValueError as exc:
                failed.append(str(exc))
        if succeeded:
            modeladmin.message_user(request, f"{succeeded} order(s) moved to '{target_status}'.")
        for message in failed:
            modeladmin.message_user(request, message, level="warning")

    action.short_description = label
    action.__name__ = f"mark_{target_status}"
    return action


class CartItemInline(TabularInline):
    model = CartItem
    extra = 0


class OrderItemInline(TabularInline):
    model = OrderItem
    extra = 0


class AbandonedCartFilter(admin.SimpleListFilter):
    title = "abandoned"
    parameter_name = "abandoned"

    def lookups(self, request, model_admin):
        return [("yes", "Idle 24h+ with items")]

    def queryset(self, request, queryset):
        if self.value() == "yes":
            from datetime import timedelta

            from django.utils import timezone

            cutoff = timezone.now() - timedelta(hours=24)
            return queryset.filter(updated_at__lt=cutoff, items__isnull=False).distinct()
        return queryset


@admin.register(Cart)
class CartAdmin(ModelAdmin):
    list_display = ("user", "item_count", "subtotal", "updated_at")
    list_filter = (AbandonedCartFilter,)
    inlines = [CartItemInline]
    readonly_fields = ("created_at", "updated_at")


@admin.register(Order)
class OrderAdmin(ModelAdmin):
    list_display = ("id", "user", "status", "payment_status", "total_amount", "created_at")
    list_filter = ("status", "payment_status")
    search_fields = ("user__username", "shipping_name", "shipping_email")
    inlines = [OrderItemInline]
    readonly_fields = ("status", "payment_status", "created_at", "updated_at")
    actions = [
        _make_transition_action(Order.STATUS_PROCESSING, "Mark selected orders as Processing"),
        _make_transition_action(Order.STATUS_SHIPPED, "Mark selected orders as Shipped"),
        _make_transition_action(Order.STATUS_DELIVERED, "Mark selected orders as Delivered"),
        _make_transition_action(Order.STATUS_CANCELLED, "Cancel selected orders"),
        _make_transition_action(Order.STATUS_RETURNED, "Mark selected orders as Returned"),
    ]


@admin.register(Payment)
class PaymentAdmin(ModelAdmin):
    list_display = ("order", "provider", "reference", "amount", "status", "created_at")
    list_filter = ("provider", "status")
    search_fields = ("reference", "order__id")
