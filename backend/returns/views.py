from rest_framework import permissions, viewsets

from .models import ReturnRequest
from .serializers import ReturnRequestSerializer


class ReturnRequestViewSet(viewsets.ModelViewSet):
    """Customers can create and view their own return requests. Approval/rejection
    is a staff action performed in the admin (via ReturnRequest.transition_to()),
    not exposed here, since it changes the parent order's state and should go
    through the same reviewed workflow as other fulfillment actions."""

    serializer_class = ReturnRequestSerializer
    # Never served (get_queryset scopes to the user); present so schema
    # generation can type the {id} path parameter instead of guessing "string".
    queryset = ReturnRequest.objects.none()
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ["get", "post", "head", "options"]  # no client-side status edits

    def get_queryset(self):
        queryset = ReturnRequest.objects.select_related("order").order_by("-created_at")
        if self.request.user.is_staff:
            return queryset
        return queryset.filter(order__user=self.request.user)
