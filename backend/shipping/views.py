from rest_framework import permissions, viewsets

from .models import ShippingZone
from .serializers import ShippingZoneSerializer


class ShippingZoneViewSet(viewsets.ReadOnlyModelViewSet):
    """Storefront-facing: lets checkout show 'delivery to Accra Metro: GHS 15,
    2-3 days' *before* the customer commits to an order, per the disclosure
    requirement in the UX guidelines."""

    serializer_class = ShippingZoneSerializer
    permission_classes = [permissions.AllowAny]
    queryset = ShippingZone.objects.filter(is_active=True).prefetch_related("pickup_stations")
