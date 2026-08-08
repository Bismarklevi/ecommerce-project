from django.contrib import admin
from unfold.admin import ModelAdmin, TabularInline

from .models import PickupStation, ShippingZone


class PickupStationInline(TabularInline):
    model = PickupStation
    extra = 0


@admin.register(ShippingZone)
class ShippingZoneAdmin(ModelAdmin):
    list_display = ("name", "tier", "base_rate", "per_kg_rate", "estimated_days_min", "estimated_days_max", "is_active")
    list_filter = ("tier", "is_active")
    inlines = [PickupStationInline]
