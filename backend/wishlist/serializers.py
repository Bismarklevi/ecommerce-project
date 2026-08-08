from rest_framework import serializers

from products.serializers import ProductListSerializer

from .models import WishlistItem


class WishlistItemSerializer(serializers.ModelSerializer):
    product_detail = ProductListSerializer(source="product", read_only=True)

    class Meta:
        model = WishlistItem
        fields = ["id", "product", "product_detail", "created_at"]
        read_only_fields = ["id", "created_at"]

    def create(self, validated_data):
        # Idempotent: re-adding an already-wishlisted product returns the existing row
        # rather than raising a uniqueness error a UI would have to special-case.
        user = self.context["request"].user
        item, _ = WishlistItem.objects.get_or_create(user=user, product=validated_data["product"])
        return item
