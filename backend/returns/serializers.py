from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from .models import ReturnRequest


class ReturnRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReturnRequest
        fields = [
            "id", "order", "reason", "status", "refund_amount",
            "staff_notes", "created_at", "updated_at",
        ]
        read_only_fields = ["status", "refund_amount", "staff_notes", "created_at", "updated_at"]

    def validate_order(self, order):
        request = self.context["request"]
        if order.user_id != request.user.id:
            raise serializers.ValidationError("You can only request a return on your own orders.")
        return order

    def create(self, validated_data):
        instance = ReturnRequest(**validated_data)
        try:
            instance.full_clean()
        except DjangoValidationError as exc:
            raise serializers.ValidationError(exc.message_dict if hasattr(exc, "message_dict") else exc.messages)
        instance.save()
        return instance
