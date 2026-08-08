from rest_framework import serializers

from users.serializers import UserSerializer

from .models import Category, Product, ProductImage, ProductVariant, Review


def _absolute_url(request, url):
    if not url:
        return ""
    if url.startswith("http"):
        return url
    if request is None:
        return url
    return request.build_absolute_uri(url)


def _resolve_image(request, file_field, static_url):
    """Prefer an uploaded file (local disk or Cloudflare R2); fall back to a
    static hotlink URL (e.g. Unsplash/Pexels) when no file has been uploaded."""
    if file_field:
        return _absolute_url(request, file_field.url)
    return static_url or ""


class CategorySerializer(serializers.ModelSerializer):
    product_count = serializers.SerializerMethodField()
    image = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = [
            "id",
            "name",
            "slug",
            "description",
            "image",
            "image_credit",
            "is_active",
            "product_count",
            "created_at",
            "updated_at",
        ]

    def get_product_count(self, obj):
        return getattr(obj, "product_count", obj.products.count())

    def get_image(self, obj):
        request = self.context.get("request")
        return _resolve_image(request, obj.image, obj.image_url)


class ProductImageSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()

    class Meta:
        model = ProductImage
        fields = ["id", "image", "alt_text", "credit", "position", "created_at", "updated_at"]

    def get_image(self, obj):
        request = self.context.get("request")
        return _resolve_image(request, obj.image, obj.image_url)


class ProductVariantSerializer(serializers.ModelSerializer):
    effective_price = serializers.SerializerMethodField()

    class Meta:
        model = ProductVariant
        fields = [
            "id",
            "product",
            "sku",
            "size",
            "color",
            "stock_quantity",
            "price",
            "effective_price",
            "is_default",
            "created_at",
            "updated_at",
        ]

    def get_effective_price(self, obj):
        return obj.effective_price


class ProductListSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    images = ProductImageSerializer(many=True, read_only=True)
    variants = ProductVariantSerializer(many=True, read_only=True)
    primary_image_url = serializers.SerializerMethodField()
    review_count = serializers.SerializerMethodField()
    average_rating = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            "id",
            "slug",
            "name",
            "short_description",
            "description",
            "base_price",
            "category",
            "images",
            "variants",
            "primary_image_url",
            "is_featured",
            "is_active",
            "review_count",
            "average_rating",
            "created_at",
            "updated_at",
        ]

    def get_primary_image_url(self, obj):
        request = self.context.get("request")
        image = obj.primary_image
        if image is None:
            return ""
        return _resolve_image(request, image.image, image.image_url)

    def get_review_count(self, obj):
        return getattr(obj, "review_count", obj.reviews.count())

    def get_average_rating(self, obj):
        return getattr(obj, "average_rating", None)


class ProductDetailSerializer(ProductListSerializer):
    reviews = serializers.SerializerMethodField()

    class Meta(ProductListSerializer.Meta):
        fields = ProductListSerializer.Meta.fields + ["reviews"]

    def get_reviews(self, obj):
        request = self.context.get("request")
        return ReviewSerializer(obj.reviews.select_related("user"), many=True, context={"request": request}).data


class ReviewSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    product_id = serializers.PrimaryKeyRelatedField(
        source="product",
        queryset=Product.objects.filter(is_active=True),
        write_only=True,
    )
    product = serializers.SerializerMethodField()

    class Meta:
        model = Review
        fields = [
            "id",
            "product_id",
            "product",
            "user",
            "rating",
            "title",
            "body",
            "is_approved",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["product", "user", "is_approved", "created_at", "updated_at"]

    def get_product(self, obj):
        return ProductListSerializer(obj.product, context=self.context).data

