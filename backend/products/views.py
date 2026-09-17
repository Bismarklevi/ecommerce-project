from django.db.models import Avg, Count
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, permissions, viewsets

from .filters import ProductFilter
from .models import Category, Product, Review
from .serializers import (
    CategorySerializer,
    ProductDetailSerializer,
    ProductListSerializer,
    ReviewSerializer,
)
from django.db.models import Prefetch
from .models import variants_in_size_order


class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = CategorySerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        return (
            Category.objects.filter(is_active=True)
            .annotate(product_count=Count("products"))
            .order_by("name")
        )


class ProductViewSet(viewsets.ReadOnlyModelViewSet):
    lookup_field = "slug"
    permission_classes = [permissions.AllowAny]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = ProductFilter
    search_fields = ["name", "short_description", "description", "category__name"]
    ordering_fields = ["base_price", "created_at", "name"]
    ordering = ["name"]

    def get_queryset(self):
        return (
            Product.objects.filter(is_active=True)
            .select_related("category")
            .prefetch_related("images", Prefetch("variants", queryset=variants_in_size_order()), "reviews__user")
            .annotate(review_count=Count("reviews"), average_rating=Avg("reviews__rating"))
            .order_by("name")
        )

    def get_serializer_class(self):
        if self.action == "retrieve":
            return ProductDetailSerializer
        return ProductListSerializer


class ReviewViewSet(viewsets.ModelViewSet):
    serializer_class = ReviewSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        queryset = Review.objects.select_related("product", "user").order_by("-created_at")
        if self.request.user.is_staff:
            return queryset
        return queryset.filter(is_approved=True)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

