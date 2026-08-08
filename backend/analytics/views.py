from drf_spectacular.utils import extend_schema
from rest_framework import permissions, serializers
from rest_framework.response import Response
from rest_framework.views import APIView

from . import services


class SalesSummarySerializer(serializers.Serializer):
    period_days = serializers.IntegerField()
    revenue = serializers.DecimalField(max_digits=12, decimal_places=2)
    paid_order_count = serializers.IntegerField()
    average_order_value = serializers.DecimalField(max_digits=12, decimal_places=2)


class SalesReportView(APIView):
    """Feeds admin/BI reporting: revenue, top SKUs, order-status breakdown over a
    configurable trailing window. Staff-only — this is business-sensitive data,
    not something a storefront customer's token should be able to read."""

    permission_classes = [permissions.IsAdminUser]

    @extend_schema(
        tags=["Analytics"],
        summary="Sales summary + top SKUs + order-status breakdown",
        responses={200: SalesSummarySerializer},
    )
    def get(self, request, *args, **kwargs):
        try:
            days = int(request.query_params.get("days", 30))
        except ValueError:
            days = 30
        days = max(1, min(days, 365))

        return Response(
            {
                "summary": services.sales_summary(days=days),
                "top_selling_variants": services.top_selling_variants(days=days),
                "order_status_breakdown": services.order_status_breakdown(),
            }
        )
