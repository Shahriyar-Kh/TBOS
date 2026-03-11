from django.utils.decorators import method_decorator
from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.views import APIView

from apps.accounts.models import User
from apps.accounts.serializers import (
    AdminUserSerializer,
    ChangePasswordSerializer,
    GoogleLoginSerializer,
    LoginSerializer,
    LogoutSerializer,
    ProfileSerializer,
    ProfileUpdateSerializer,
    RegisterSerializer,
    UserSerializer,
)
from apps.accounts.services.account_service import AccountService
from apps.core.exceptions import api_success
from apps.core.pagination import StandardPagination
from apps.core.permissions import IsAdmin
from apps.core.ratelimits import AuthRateThrottle, ratelimit_auth


@method_decorator(ratelimit_auth, name="dispatch")
class RegisterView(generics.CreateAPIView):
    """POST /api/v1/auth/register/"""

    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]
    throttle_classes = [AuthRateThrottle]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user, auth_payload = AccountService.register_user(serializer.validated_data)
        auth_payload["user"] = UserSerializer(user, context={"request": request}).data
        return api_success(
            data=auth_payload,
            message="User registered successfully.",
            status_code=status.HTTP_201_CREATED,
        )


@method_decorator(ratelimit_auth, name="dispatch")
class LoginView(APIView):
    """POST /api/v1/auth/login/"""

    permission_classes = [AllowAny]
    throttle_classes = [AuthRateThrottle]

    def post(self, request, *args, **kwargs):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        payload = AccountService.login_user(request=request, **serializer.validated_data)
        return api_success(data=payload, message="Login successful.")


@method_decorator(ratelimit_auth, name="dispatch")
class GoogleLoginView(APIView):
    """POST /api/v1/auth/google-login/"""

    permission_classes = [AllowAny]
    throttle_classes = [AuthRateThrottle]

    def post(self, request, *args, **kwargs):
        serializer = GoogleLoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        created, payload = AccountService.handle_google_login(
            serializer.validated_data["id_token"]
        )
        message = "Google login successful." if not created else "Google account created successfully."
        return api_success(data=payload, message=message)


class LogoutView(APIView):
    """POST /api/v1/auth/logout/"""

    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = LogoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        AccountService.logout_user(serializer.validated_data["refresh_token"])
        return api_success(message="Logout successful.")


class MeView(APIView):
    """GET /api/v1/auth/me/"""

    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        return api_success(
            data=UserSerializer(request.user, context={"request": request}).data,
            message="User retrieved successfully.",
        )


class ProfileView(APIView):
    """GET /api/v1/auth/profile/"""

    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        profile = AccountService.create_profile(request.user)
        return api_success(
            data=ProfileSerializer(profile, context={"request": request}).data,
            message="Profile retrieved successfully.",
        )


class ProfileUpdateView(generics.UpdateAPIView):
    """PUT/PATCH /api/v1/auth/profile/update/"""

    serializer_class = ProfileUpdateSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return AccountService.create_profile(self.request.user)

    def update(self, request, *args, **kwargs):
        serializer = self.get_serializer(
            self.get_object(),
            data=request.data,
            partial=request.method == "PATCH",
        )
        serializer.is_valid(raise_exception=True)
        profile = AccountService.update_profile(request.user, serializer.validated_data)
        return api_success(
            data=ProfileSerializer(profile, context={"request": request}).data,
            message="Profile updated successfully.",
        )


class ChangePasswordView(generics.UpdateAPIView):
    """PUT /api/v1/auth/change-password/"""

    serializer_class = ChangePasswordSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user

    def update(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        AccountService.change_password(request.user, serializer.validated_data["new_password"])
        return api_success(message="Password changed successfully.")


class BaseAdminUserListView(generics.ListAPIView):
    serializer_class = AdminUserSerializer
    permission_classes = [IsAuthenticated, IsAdmin]
    pagination_class = StandardPagination
    role_filter = None

    def get_queryset(self):
        return AccountService.get_users(role=self.role_filter)

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return api_success(
                data={
                    "count": self.paginator.page.paginator.count,
                    "next": self.paginator.get_next_link(),
                    "previous": self.paginator.get_previous_link(),
                    "results": serializer.data,
                },
                message="Users retrieved successfully.",
            )

        serializer = self.get_serializer(queryset, many=True)
        return api_success(data=serializer.data, message="Users retrieved successfully.")


class AdminUsersView(BaseAdminUserListView):
    """GET /api/v1/admin/users/"""


class AdminInstructorsView(BaseAdminUserListView):
    """GET /api/v1/admin/instructors/"""

    role_filter = User.Role.INSTRUCTOR


class AdminStudentsView(BaseAdminUserListView):
    """GET /api/v1/admin/students/"""

    role_filter = User.Role.STUDENT


class AdminUserStatusView(APIView):
    """POST /api/v1/admin/users/{user_id}/{action}/"""

    permission_classes = [IsAuthenticated, IsAdmin]

    def post(self, request, user_id, action, *args, **kwargs):
        user = generics.get_object_or_404(User, id=user_id)
        if action == "activate":
            AccountService.activate_user(user)
            message = "User activated successfully."
        else:
            AccountService.deactivate_user(user)
            message = "User deactivated successfully."
        return api_success(
            data=AdminUserSerializer(user, context={"request": request}).data,
            message=message,
        )
