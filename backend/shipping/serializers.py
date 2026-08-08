from rest_framework import serializers

from .models import PickupStation, ShippingZone


class PickupStationSerializer(serializers.ModelSerializer):
    class Meta:
        model = PickupStation
        fields = ["id", "name", "address", "contact_phone"]


class ShippingZoneSerializer(serializers.ModelSerializer):
    pickup_stations = PickupStationSerializer(many=True, read_only=True)
    estimated_rate = serializers.SerializerMethodField()

    class Meta:
        model = ShippingZone
        fields = [
            "id", "name", "tier", "base_rate", "per_kg_rate",
            "estimated_days_min", "estimated_days_max",
            "supports_pickup_station", "pickup_stations", "estimated_rate",
        ]

    def get_estimated_rate(self, obj) -> str:
        return str(obj.calculate_rate())
