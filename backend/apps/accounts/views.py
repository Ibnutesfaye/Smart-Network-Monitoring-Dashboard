from typing import ClassVar

from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.utils.decorators import method_decorator
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django_ratelimit.decorators import ratelimit
from rest_framework import generics, status, viewsets
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView

from apps.audit.utils import log_activity

from .permissions import IsAdministrator
from .serializers import (
    PasswordChangeSerializer,
    PasswordResetConfirmSerializer,
    PasswordResetRequestSerializer,
    RegisterSerializer,
    UserCreateSerializer,
    UserSerializer,
    UserUpdateSerializer,
)

User = get_user_model()


@method_decorator(ratelimit(key="ip", rate="5/m", method="POST", block=True), name="dispatch")
class LoginView(TokenObtainPairView):
    permission_classes: ClassVar = [AllowAny]

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        if response.status_code == 200:
            user = User.objects.get(username=request.data.get("username"))
            log_activity(user, "login", "User logged in", request)
        return response


class LogoutView(APIView):
    def post(self, request):
        try:
            refresh = request.data.get("refresh")
            if refresh:
                token = RefreshToken(refresh)
                token.blacklist()
            log_activity(request.user, "logout", "User logged out", request)
            return Response({"detail": "Logged out successfully."})
        except Exception:
            return Response({"detail": "Invalid token."}, status=status.HTTP_400_BAD_REQUEST)


class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes: ClassVar = [IsAdministrator]


class PasswordResetRequestView(APIView):
    permission_classes: ClassVar = [AllowAny]

    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"]
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({"detail": "If the email exists, a reset link was sent."})
        token = default_token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        reset_link = f"{request.build_absolute_uri('/')}reset-password?uid={uid}&token={token}"
        send_mail(
            "Password Reset - SNMADMDCP",
            f"Use this link to reset your password: {reset_link}",
            None,
            [email],
            fail_silently=True,
        )
        return Response({"detail": "If the email exists, a reset link was sent."})


class PasswordResetConfirmView(APIView):
    permission_classes: ClassVar = [AllowAny]

    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        uid = request.data.get("uid")
        token = serializer.validated_data["token"]
        new_password = serializer.validated_data["new_password"]
        try:
            user_id = force_str(urlsafe_base64_decode(uid))
            user = User.objects.get(pk=user_id)
        except (User.DoesNotExist, ValueError, TypeError):
            return Response({"detail": "Invalid reset link."}, status=status.HTTP_400_BAD_REQUEST)
        if not default_token_generator.check_token(user, token):
            return Response({"detail": "Invalid or expired token."}, status=status.HTTP_400_BAD_REQUEST)
        user.set_password(new_password)
        user.save()
        return Response({"detail": "Password reset successful."})


class PasswordChangeView(APIView):
    def post(self, request):
        serializer = PasswordChangeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        if not request.user.check_password(serializer.validated_data["old_password"]):
            return Response({"old_password": "Wrong password."}, status=status.HTTP_400_BAD_REQUEST)
        request.user.set_password(serializer.validated_data["new_password"])
        request.user.save()
        log_activity(request.user, "password_change", "Password changed", request)
        return Response({"detail": "Password updated."})


class ProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = UserSerializer

    def get_object(self):
        return self.request.user

    def get_serializer_class(self):
        if self.request.method in ("PUT", "PATCH"):
            return UserUpdateSerializer
        return UserSerializer


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    permission_classes: ClassVar = [IsAdministrator]

    def get_serializer_class(self):
        if self.action == "create":
            return UserCreateSerializer
        if self.action in ("update", "partial_update"):
            return UserUpdateSerializer
        return UserSerializer

    def perform_destroy(self, instance):
        log_activity(self.request.user, "user_delete", f"Deleted user {instance.username}", self.request)
        instance.delete()

    def perform_create(self, serializer):
        user = serializer.save()
        log_activity(self.request.user, "user_create", f"Created user {user.username}", self.request)
