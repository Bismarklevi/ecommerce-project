from django.db import transaction
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from products.models import ProductVariant
from products.serializers import ProductVariantSerializer, _resolve_image
from users.serializers import UserSerializer

from .models import Cart, CartItem, Order, OrderItem, Payment
from .services import InsufficientStockError, reserve_stock_for_order


class CartItemSerializer(serializers.ModelSerializer):
    product_variant = ProductVariantSerializer(read_only=True)
    product_variant_id = serializers.PrimaryKeyRelatedField(
        source="product_variant",
        queryset=ProductVariant.objects.select_related("product"),
        write_only=True,
    )
    unit_price = serializers.SerializerMethodField()
    line_total = serializers.SerializerMethodField()
    product_name = serializers.SerializerMethodField()
    product_slug = serializers.SerializerMethodField()
    product_image = serializers.SerializerMethodField()

    class Meta:
        model = CartItem
        fields = [
            "id",
            "product_variant",
            "product_variant_id",
            "quantity",
            "unit_price",
            "line_total",
            "product_name",
            "product_slug",
            "product_image",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]

    @extend_schema_field(serializers.DecimalField(max_digits=10, decimal_places=2))
    def get_unit_price(self, obj):
        return obj.unit_price

    @extend_schema_field(serializers.DecimalField(max_digits=10, decimal_places=2))
    def get_line_total(self, obj):
        return obj.line_total

    @extend_schema_field(serializers.CharField())
    def get_product_name(self, obj):
        return obj.product_variant.product.name

    @extend_schema_field(serializers.CharField())
    def get_product_slug(self, obj):
        return obj.product_variant.product.slug

    @extend_schema_field(serializers.URLField(allow_blank=True))
    def get_product_image(self, obj):
        request = self.context.get("request")
        image = obj.product_variant.product.primary_image
        if image is None:
            return ""
        return _resolve_image(request, image.image, image.image_url)


class CartSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    items = CartItemSerializer(many=True, required=False)
    item_count = serializers.SerializerMethodField()
    subtotal = serializers.SerializerMethodField()

    class Meta:
        model = Cart
        fields = ["id", "user", "items", "item_count", "subtotal", "created_at", "updated_at"]
        read_only_fields = ["created_at", "updated_at"]

    @extend_schema_field(serializers.IntegerField())
    def get_item_count(self, obj):
        return obj.item_count

    @extend_schema_field(serializers.DecimalField(max_digits=10, decimal_places=2))
    def get_subtotal(self, obj):
        return obj.subtotal

    def create(self, validated_data):
        items_data = validated_data.pop("items", [])
        cart = Cart.objects.create(**validated_data)
        for item_data in items_data:
            CartItem.objects.create(cart=cart, **item_data)
        return cart


class OrderItemSerializer(serializers.ModelSerializer):
    product_variant = ProductVariantSerializer(read_only=True)
    product_variant_id = serializers.PrimaryKeyRelatedField(
        source="product_variant",
        queryset=ProductVariant.objects.select_related("product"),
        write_only=True,
    )

    class Meta:
        model = OrderItem
        fields = [
            "id",
            "product_variant",
            "product_variant_id",
            "product_name",
            "product_sku",
            "size",
            "color",
            "quantity",
            "unit_price",
            "line_total",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "product_name",
            "product_sku",
            "size",
            "color",
            "unit_price",
            "line_total",
            "created_at",
            "updated_at",
        ]


class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = [
            "id",
            "order",
            "provider",
            "reference",
            "amount",
            "status",
            "raw_response",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]


class OrderSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    items = OrderItemSerializer(many=True)
    payment = PaymentSerializer(read_only=True)
    item_count = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = [
            "id",
            "user",
            "status",
            "payment_status",
            "total_amount",
            "shipping_name",
            "shipping_email",
            "shipping_phone",
            "shipping_address",
            "shipping_cost",
            "tracking_number",
            "notes",
            "items",
            "payment",
            "item_count",
            "created_at",
            "updated_at",
            "delivered_at",
        ]
        read_only_fields = [
            "total_amount",
            "shipping_cost",
            "tracking_number",
            "created_at",
            "updated_at",
            "delivered_at",
        ]

    @extend_schema_field(serializers.IntegerField())
    def get_item_count(self, obj):
        return obj.item_count

    def create(self, validated_data):
        items_data = validated_data.pop("items", [])
        if not items_data:
            raise serializers.ValidationError({"items": "An order must contain at least one item."})

        with transaction.atomic():
            order = Order.objects.create(**validated_data)
            total_amount = 0
            for item_data in items_data:
                product_variant = item_data.pop("product_variant")
                quantity = item_data.get("quantity", 1)
                order_item = OrderItem.objects.create(
                    order=order,
                    product_variant=product_variant,
                    product_name=product_variant.product.name,
                    product_sku=product_variant.sku,
                    size=product_variant.size,
                    color=product_variant.color,
                    quantity=quantity,
                    unit_price=product_variant.effective_price,
                    line_total=product_variant.effective_price * quantity,
                )
                total_amount += order_item.line_total
            order.total_amount = total_amount
            order.save(update_fields=["total_amount"])

            # Reserve stock inside the same transaction as order creation: if stock
            # is insufficient, the whole order creation rolls back — the customer
            # never ends up with a "confirmed" order for units that don't exist.
            try:
                reserve_stock_for_order(order)
            except InsufficientStockError as exc:
                raise serializers.ValidationError({"items": str(exc)}) from exc

        return order

