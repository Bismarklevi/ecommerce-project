from decimal import Decimal

from django.test import TestCase

from .models import ShippingZone


class ShippingRateTests(TestCase):
    def test_flat_rate_with_no_weight(self):
        zone = ShippingZone.objects.create(
            name="Accra Metro", tier=ShippingZone.TIER_ACCRA_METRO,
            base_rate=Decimal("15.00"), per_kg_rate=Decimal("2.00"),
        )
        self.assertEqual(zone.calculate_rate(), Decimal("15.00"))

    def test_rate_scales_with_weight(self):
        zone = ShippingZone.objects.create(
            name="Rural", tier=ShippingZone.TIER_RURAL,
            base_rate=Decimal("25.00"), per_kg_rate=Decimal("5.00"),
        )
        self.assertEqual(zone.calculate_rate(Decimal("3.00")), Decimal("40.00"))
