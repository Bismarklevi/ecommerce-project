from decimal import Decimal

from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from .models import Coupon


class CouponValidateSerializer(serializers.Serializer):
    code = serializers.CharField()
    order_subtotal = serializers.DecimalField(max_digits=10, decimal_places=2)

    def validate(self, attrs):
        try:
            coupon = Coupon.objects.get(code__iexact=attrs["code"])
        except Coupon.DoesNotExist as exc:
            raise serializers.ValidationError({"code": "Coupon not found."}) from exc

        request = self.context.get("request")
        user = getattr(request, "user", None)

        try:
            coupon.validate_for(user=user, order_subtotal=attrs["order_subtotal"])
        except DjangoValidationError as exc:
            raise serializers.ValidationError({"code": exc.messages}) from exc

        attrs["coupon"] = coupon
        attrs["discount_amount"] = coupon.compute_discount(attrs["order_subtotal"])
        return attrs
