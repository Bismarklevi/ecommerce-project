from drf_spectacular.utils import extend_schema_view
from rest_framework import permissions, viewsets

from .models import WishlistItem
from .serializers import WishlistItemSerializer
from django.db.models import Prefetch
from products.models import variants_in_size_order


@extend_schema_view()
class WishlistViewSet(viewsets.ModelViewSet):
    """List, add, and remove products from the current user's wishlist."""

    serializer_class = WishlistItemSerializer
    permission_classes = [permissions.IsAuthenticated]
    # Never served (get_queryset scopes to the user); present so schema
    # generation can type the {id} path parameter instead of guessing "string".
    queryset = WishlistItem.objects.none()

    def get_queryset(self):
        return (
            WishlistItem.objects.filter(user=self.request.user)
            .select_related("product", "product__category")
            .prefetch_related("product__images", Prefetch("product__variants", queryset=variants_in_size_order()))
        )

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
