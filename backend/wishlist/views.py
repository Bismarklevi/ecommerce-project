from drf_spectacular.utils import extend_schema_view
from rest_framework import permissions, viewsets

from .models import WishlistItem
from .serializers import WishlistItemSerializer


@extend_schema_view()
class WishlistViewSet(viewsets.ModelViewSet):
    """List, add, and remove products from the current user's wishlist."""

    serializer_class = WishlistItemSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return (
            WishlistItem.objects.filter(user=self.request.user)
            .select_related("product", "product__category")
            .prefetch_related("product__images", "product__variants")
        )

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
