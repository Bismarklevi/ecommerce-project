from drf_spectacular.utils import extend_schema
from rest_framework import permissions, serializers
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import CouponValidateSerializer


class CouponValidateResultSerializer(serializers.Serializer):
    code = serializers.CharField()
    discount_amount = serializers.DecimalField(max_digits=10, decimal_places=2)


class CouponValidateView(APIView):
    """Preview a coupon's discount before checkout, without redeeming it.
    Redemption itself only happens inside CheckoutView, atomically with payment
    initiation, so a validated-but-unused coupon never consumes a usage slot."""

    permission_classes = [permissions.AllowAny]

    @extend_schema(
        tags=["Promotions"],
        summary="Validate a coupon code against an order subtotal (no redemption)",
        request=CouponValidateSerializer,
        responses={200: CouponValidateResultSerializer},
    )
    def post(self, request, *args, **kwargs):
        serializer = CouponValidateSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        return Response(
            {
                "code": serializer.validated_data["coupon"].code,
                "discount_amount": serializer.validated_data["discount_amount"],
            }
        )
