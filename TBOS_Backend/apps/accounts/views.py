from django.contrib.auth import get_user_model
from rest_framework import generics, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from apps.core.pagination import StandardPagination
from apps.core.permissions import IsAdmin
from apps.accounts.serializers import (
    AdminUserSerializer,
    ChangePasswordSerializer,
    RegisterSerializer,
    UserSerializer,
    UserUpdateSerializer,
)

User = get_user_model()


# ──────────────────────────────────────────────
# Auth endpoints
# ──────────────────────────────────────────────
class RegisterView(generics.CreateAPIView):
    """POST /api/v1/accounts/register/"""
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(
            {
                "success": True,
                "message": "Registration successful.",
                "data": UserSerializer(user).data,
            },
            status=status.HTTP_201_CREATED,
        )


class LoginView(TokenObtainPairView):
    """POST /api/v1/accounts/login/"""
    permission_classes = [AllowAny]


class TokenRefresh(TokenRefreshView):
    """POST /api/v1/accounts/token/refresh/"""
    permission_classes = [AllowAny]


# ──────────────────────────────────────────────
# Profile / self-service
# ──────────────────────────────────────────────
class MeView(generics.RetrieveUpdateAPIView):
    """GET/PATCH /api/v1/accounts/me/"""
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.request.method in ("PATCH", "PUT"):
            return UserUpdateSerializer
        return UserSerializer

    def get_object(self):
        return self.request.user


class ChangePasswordView(generics.UpdateAPIView):
    """PUT /api/v1/accounts/change-password/"""
    serializer_class = ChangePasswordSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user

    def update(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        request.user.set_password(serializer.validated_data["new_password"])
        request.user.save()
        return Response(
            {"success": True, "message": "Password changed successfully."}
        )


# ──────────────────────────────────────────────
# Admin user management
# ──────────────────────────────────────────────
class AdminUserViewSet(viewsets.ModelViewSet):
    """
    Admin-only CRUD on all users.
    GET    /api/v1/accounts/admin/users/
    GET    /api/v1/accounts/admin/users/{id}/
    PATCH  /api/v1/accounts/admin/users/{id}/
    DELETE /api/v1/accounts/admin/users/{id}/
    """
    queryset = User.objects.select_related("profile").all()
    serializer_class = AdminUserSerializer
    permission_classes = [IsAuthenticated, IsAdmin]
    pagination_class = StandardPagination
    http_method_names = ["get", "patch", "delete", "head", "options"]
    lookup_field = "id"

    def get_queryset(self):
        qs = super().get_queryset()
        role = self.request.query_params.get("role")
        if role:
            qs = qs.filter(role=role)
        return qs

    @action(detail=True, methods=["post"])
    def deactivate(self, request, id=None):
        user = self.get_object()
        user.is_active = False
        user.save(update_fields=["is_active"])
        return Response({"success": True, "message": "User deactivated."})

    @action(detail=True, methods=["post"])
    def activate(self, request, id=None):
        user = self.get_object()
        user.is_active = True
        user.save(update_fields=["is_active"])
        return Response({"success": True, "message": "User activated."})
