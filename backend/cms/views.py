from django.db.models import Q
from django.utils import timezone
from rest_framework import permissions, viewsets

from .models import Banner, ContentBlock
from .serializers import BannerSerializer, ContentBlockSerializer


class BannerViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = BannerSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        now = timezone.now()
        active_window = (Q(starts_at__isnull=True) | Q(starts_at__lte=now)) & (
            Q(ends_at__isnull=True) | Q(ends_at__gte=now)
        )
        return Banner.objects.filter(is_active=True).filter(active_window).order_by("position", "-created_at")


class ContentBlockViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = ContentBlockSerializer
    permission_classes = [permissions.AllowAny]
    lookup_field = "key"
    queryset = ContentBlock.objects.filter(is_active=True)
