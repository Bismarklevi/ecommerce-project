import logging

from django.contrib.auth import authenticate, get_user_model, login, logout
from django.contrib.auth.tokens import default_token_generator
from django.conf import settings
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from drf_spectacular.utils import extend_schema
from rest_framework import permissions, serializers, status, viewsets
from rest_framework.authtoken.models import Token
from rest_framework.response import Response
from rest_framework.views import APIView

from .mail import PlainAsciiEmailMessage
from .models import Address
from .throttling import LoginRateThrottle, PasswordResetRateThrottle, RegisterRateThrottle
from .serializers import (
    AddressSerializer,
    ChangePasswordSerializer,
    PasswordResetConfirmSerializer,
    PasswordResetRequestSerializer,
    ProfileUpdateSerializer,
    RegisterSerializer,
    UserSerializer,
)

User = get_user_model()
logger = logging.getLogger(__name__)


def _user_response_with_token(user, status_code=200):
    """The frontend's login/register API routes read `data.token` and store it
    in an httpOnly cookie (see frontend/app/api/auth/login/route.ts) -- so every
    endpoint that starts a session needs to hand one back alongside the user."""
    token, _ = Token.objects.get_or_create(user=user)
    return Response({**UserSerializer(user).data, "token": token.key}, status=status_code)


class UserViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = User.objects.all().order_by("username")
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAdminUser]


class CurrentUserView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = UserSerializer

    def get(self, request, *args, **kwargs):
        return Response(UserSerializer(request.user).data)

    @extend_schema(tags=["Account"], request=ProfileUpdateSerializer, responses={200: UserSerializer})
    def patch(self, request, *args, **kwargs):
        serializer = ProfileUpdateSerializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(UserSerializer(request.user).data)


class RegisterView(APIView):
    """Public account creation. Also logs the new user into a Django session
    (useful for the admin/browsable API), but the token in the response body is
    what the Next.js frontend actually authenticates with on every later request."""

    permission_classes = [permissions.AllowAny]
    throttle_classes = [RegisterRateThrottle]

    @extend_schema(tags=["Auth"], request=RegisterSerializer, responses={201: UserSerializer})
    def post(self, request, *args, **kwargs):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        login(request, user)
        return _user_response_with_token(user, status_code=201)


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)


class LoginView(APIView):
    permission_classes = [permissions.AllowAny]
    throttle_classes = [LoginRateThrottle]

    @extend_schema(tags=["Auth"], request=LoginSerializer, responses={200: UserSerializer, 401: None})
    def post(self, request, *args, **kwargs):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = authenticate(
            request,
            username=serializer.validated_data["username"],
            password=serializer.validated_data["password"],
        )
        if user is None:
            return Response({"detail": "Invalid credentials."}, status=401)
        login(request, user)
        return _user_response_with_token(user)


class LogoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(tags=["Auth"], request=None, responses={204: None})
    def post(self, request, *args, **kwargs):
        # Revoke the bearer token so the httpOnly cookie the frontend clears
        # can't be replayed even if it leaked before the client-side clear ran.
        Token.objects.filter(user=request.user).delete()
        logout(request)
        return Response(status=204)


class ChangePasswordView(APIView):
    """Password change for an already signed-in user (they supply their current
    password). Revokes their existing token afterwards so a device that had the
    old token cached can't keep acting as them -- they'll need to sign in again
    with the new password, which is the same trust model LogoutView relies on."""

    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(tags=["Account"], request=ChangePasswordSerializer, responses={204: None, 400: None})
    def post(self, request, *args, **kwargs):
        serializer = ChangePasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        if not request.user.check_password(serializer.validated_data["current_password"]):
            return Response({"detail": "Current password is incorrect."}, status=status.HTTP_400_BAD_REQUEST)

        request.user.set_password(serializer.validated_data["new_password"])
        request.user.save(update_fields=["password"])
        Token.objects.filter(user=request.user).delete()
        token = Token.objects.create(user=request.user)
        return Response({"token": token.key}, status=status.HTTP_200_OK)


class PasswordResetRequestView(APIView):
    """Starts the 'forgot password' flow. Always responds the same way whether or
    not the email matches an account -- this is deliberate: a different response
    for unknown emails would let anyone enumerate registered addresses."""

    permission_classes = [permissions.AllowAny]
    throttle_classes = [PasswordResetRateThrottle]

    @extend_schema(tags=["Auth"], request=PasswordResetRequestSerializer, responses={200: None})
    def post(self, request, *args, **kwargs):
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"]

        try:
            user = User.objects.get(email__iexact=email)
        except User.DoesNotExist:
            user = None

        if user is not None:
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)
            reset_url = f"{settings.FRONTEND_URL}/reset-password?uid={uid}&token={token}"
            try:
                PlainAsciiEmailMessage(
                    subject="Reset your password",
                    body=(
                        f"Hi {user.get_full_name() or user.username},\n\n"
                        f"Use the link below to reset your password. This link expires soon "
                        f"and can only be used once.\n\n{reset_url}\n\n"
                        "If you didn't request this, you can safely ignore this email."
                    ),
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    to=[user.email],
                ).send(fail_silently=False)
            except Exception:
                # Don't leak whether sending failed -- avoids both enumeration and
                # confusing the user with an SMTP error they can't act on.
                logger.exception("Failed to send password reset email to %s", user.email)

        return Response({"detail": "If that email exists, a reset link has been sent."})


class PasswordResetConfirmView(APIView):
    permission_classes = [permissions.AllowAny]
    # No email/username in the confirm payload, so this throttle keys on the
    # client IP -- caps brute-forcing of the reset token.
    throttle_classes = [PasswordResetRateThrottle]

    @extend_schema(tags=["Auth"], request=PasswordResetConfirmSerializer, responses={200: None, 400: None})
    def post(self, request, *args, **kwargs):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            uid = force_str(urlsafe_base64_decode(serializer.validated_data["uid"]))
            user = User.objects.get(pk=uid)
        except (User.DoesNotExist, ValueError, TypeError, OverflowError):
            return Response({"detail": "This reset link is invalid."}, status=status.HTTP_400_BAD_REQUEST)

        if not default_token_generator.check_token(user, serializer.validated_data["token"]):
            return Response(
                {"detail": "This reset link is invalid or has expired."}, status=status.HTTP_400_BAD_REQUEST
            )

        user.set_password(serializer.validated_data["new_password"])
        user.save(update_fields=["password"])
        # Any token issued before the reset is now void, same rationale as
        # ChangePasswordView -- a leaked old token shouldn't survive a reset.
        Token.objects.filter(user=user).delete()
        return Response({"detail": "Password has been reset. You can now sign in."})


class AddressViewSet(viewsets.ModelViewSet):
    """CRUD for a customer's saved addresses. Scoped to the signed-in user via
    get_queryset -- the same pattern CartItemViewSet uses -- so nobody can read or
    edit another customer's address by guessing an id."""

    serializer_class = AddressSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Address.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
