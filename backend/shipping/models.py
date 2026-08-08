from decimal import Decimal

from django.db import models


class ShippingZone(models.Model):
    """Ghana delivery is not one flat rate — Accra/Kumasi metro, other regional
    capitals, and rural areas have meaningfully different logistics costs and
    lead times. Modeling this explicitly (rather than a single flat shipping fee)
    is what makes the checkout's shipping cost line item honest."""

    TIER_ACCRA_METRO = "accra_metro"
    TIER_KUMASI_METRO = "kumasi_metro"
    TIER_REGIONAL = "regional"
    TIER_RURAL = "rural"

    TIER_CHOICES = [
        (TIER_ACCRA_METRO, "Accra Metro"),
        (TIER_KUMASI_METRO, "Kumasi Metro"),
        (TIER_REGIONAL, "Other Regional Capital"),
        (TIER_RURAL, "Rural / Remote"),
    ]

    name = models.CharField(max_length=120)
    tier = models.CharField(max_length=20, choices=TIER_CHOICES, unique=True)
    base_rate = models.DecimalField(max_digits=8, decimal_places=2)
    per_kg_rate = models.DecimalField(max_digits=8, decimal_places=2, default=Decimal("0.00"))
    estimated_days_min = models.PositiveSmallIntegerField(default=1)
    estimated_days_max = models.PositiveSmallIntegerField(default=3)
    supports_pickup_station = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["tier"]

    def __str__(self):
        return self.name

    def calculate_rate(self, weight_kg: Decimal = Decimal("0.00")) -> Decimal:
        return self.base_rate + (self.per_kg_rate * weight_kg)


class PickupStation(models.Model):
    zone = models.ForeignKey(ShippingZone, on_delete=models.CASCADE, related_name="pickup_stations")
    name = models.CharField(max_length=150)
    address = models.TextField()
    contact_phone = models.CharField(max_length=32, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["zone", "name"]

    def __str__(self):
        return f"{self.name} ({self.zone.name})"
