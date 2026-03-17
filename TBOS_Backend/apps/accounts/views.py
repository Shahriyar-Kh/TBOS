from django.utils.decorators import method_decorator
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiExample, OpenApiParameter, extend_schema, extend_schema_view, inline_serializer
from rest_framework import generics, serializers, status
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
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
from apps.core.api_docs import (
    AUTH_GUIDE,
    AUTH_RATE_LIMIT_NOTE,
    PAGE_PARAM,
    PAGE_SIZE_PARAM,
    ROLE_ACCESS_GUIDE,
    USER_EXAMPLE,
    paginated_response,
    standard_error_responses,
    success_example,
    success_response,
)
from apps.core.exceptions import api_success
from apps.core.pagination import StandardPagination
from apps.core.permissions import IsAdmin
from apps.core.ratelimits import AuthRateThrottle, ratelimit_auth


AuthPayloadSerializer = inline_serializer(
    name="AuthPayloadSerializer",
    fields={
        "access_token": serializers.CharField(),
        "refresh_token": serializers.CharField(),
        "user_role": serializers.CharField(),
        "user": UserSerializer(),
    },
)

MessageOnlySerializer = inline_serializer(
    name="MessageOnlySerializer",
    fields={},
)

UserStatusActionParameter = OpenApiParameter(
    name="action",
    type=OpenApiTypes.STR,
    location=OpenApiParameter.PATH,
    enum=["activate", "deactivate"],
    description="Administrative action to apply to the target user account.",
)


@method_decorator(ratelimit_auth, name="dispatch")
@extend_schema_view(
    post=extend_schema(
        tags=["Accounts"],
        summary="Register a new student or instructor",
        description=(
            "Create a TBOS user account and return fresh JWT access and refresh tokens. "
            f"{AUTH_RATE_LIMIT_NOTE}\n\n"
            "Self-registration is limited to the student and instructor roles. "
            "Admin accounts must be provisioned internally."
        ),
        request=RegisterSerializer,
        responses={
            201: success_response(
                "RegisterResponse",
                AuthPayloadSerializer,
                description="Account created successfully.",
                examples=[
                    success_example(
                        "RegisterSuccess",
                        "User registered successfully.",
                        {
                            "access_token": "eyJhbGciOi...access",
                            "refresh_token": "eyJhbGciOi...refresh",
                            "user_role": "student",
                            "user": USER_EXAMPLE,
                        },
                    )
                ],
            ),
            **standard_error_responses(400, 429, 500),
        },
        examples=[
            OpenApiExample(
                "RegisterRequest",
                value={
                    "first_name": "Amina",
                    "last_name": "Yusuf",
                    "email": "amina.student@tbos.dev",
                    "username": "amina.student",
                    "password": "StrongPass!123",
                    "confirm_password": "StrongPass!123",
                    "role": "student",
                },
                request_only=True,
            )
        ],
    )
)
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
@extend_schema_view(
    post=extend_schema(
        tags=["Accounts"],
        summary="Log in with email and password",
        description=(
            "Authenticate an existing TBOS account and return JWT tokens for subsequent API access. "
            f"{AUTH_RATE_LIMIT_NOTE}"
        ),
        request=LoginSerializer,
        responses={
            200: success_response(
                "LoginResponse",
                AuthPayloadSerializer,
                description="Login completed successfully.",
                examples=[
                    success_example(
                        "LoginSuccess",
                        "Login successful.",
                        {
                            "access_token": "eyJhbGciOi...access",
                            "refresh_token": "eyJhbGciOi...refresh",
                            "user_role": "student",
                            "user": USER_EXAMPLE,
                        },
                    )
                ],
            ),
            **standard_error_responses(400, 401, 429, 500),
        },
        examples=[
            OpenApiExample(
                "LoginRequest",
                value={
                    "email": "amina.student@tbos.dev",
                    "password": "StrongPass!123",
                },
                request_only=True,
            )
        ],
    )
)
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
@extend_schema_view(
    post=extend_schema(
        tags=["Accounts"],
        summary="Log in with Google",
        description=(
            "Exchange a Google ID token for a TBOS JWT session. "
            "If the user does not already exist, TBOS provisions a verified student account automatically. "
            f"{AUTH_RATE_LIMIT_NOTE}"
        ),
        request=GoogleLoginSerializer,
        responses={
            200: success_response(
                "GoogleLoginResponse",
                AuthPayloadSerializer,
                description="Google login completed successfully.",
                examples=[
                    success_example(
                        "GoogleLoginSuccess",
                        "Google login successful.",
                        {
                            "access_token": "eyJhbGciOi...access",
                            "refresh_token": "eyJhbGciOi...refresh",
                            "user_role": "student",
                            "user": {**USER_EXAMPLE, "google_account": True, "is_verified": True},
                        },
                    )
                ],
            ),
            **standard_error_responses(400, 401, 429, 500),
        },
        examples=[
            OpenApiExample(
                "GoogleLoginRequest",
                value={"id_token": "google-issued-id-token"},
                request_only=True,
            )
        ],
    )
)
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


@extend_schema_view(
    post=extend_schema(
        tags=["Accounts"],
        summary="Log out and blacklist refresh token",
        description=f"Invalidate a refresh token so it can no longer be used to mint new access tokens.\n\n{AUTH_GUIDE}",
        request=LogoutSerializer,
        responses={
            200: success_response(
                "LogoutResponse",
                MessageOnlySerializer,
                description="Logout completed successfully.",
                examples=[success_example("LogoutSuccess", "Logout successful.", {})],
            ),
            **standard_error_responses(400, 401, 500),
        },
    )
)
class LogoutView(APIView):
    """POST /api/v1/auth/logout/"""

    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = LogoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        AccountService.logout_user(serializer.validated_data["refresh_token"])
        return api_success(message="Logout successful.")


@extend_schema_view(
    get=extend_schema(
        tags=["Accounts"],
        summary="Get current authenticated user",
        description=f"Return the authenticated account and nested profile metadata.\n\n{AUTH_GUIDE}",
        responses={
            200: success_response(
                "CurrentUserResponse",
                UserSerializer,
                description="Current user retrieved successfully.",
                examples=[success_example("CurrentUser", "User retrieved successfully.", USER_EXAMPLE)],
            ),
            **standard_error_responses(401, 500),
        },
    )
)
class MeView(APIView):
    """GET /api/v1/auth/me/"""

    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        return api_success(
            data=UserSerializer(request.user, context={"request": request}).data,
            message="User retrieved successfully.",
        )


@extend_schema_view(
    get=extend_schema(
        tags=["Accounts"],
        summary="Get current user profile",
        description=f"Return the profile resource associated with the current authenticated user.\n\n{AUTH_GUIDE}",
        responses={
            200: success_response(
                "ProfileResponse",
                ProfileSerializer,
                description="Profile retrieved successfully.",
                examples=[
                    success_example(
                        "ProfileSuccess",
                        "Profile retrieved successfully.",
                        USER_EXAMPLE["profile"],
                    )
                ],
            ),
            **standard_error_responses(401, 500),
        },
    )
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


@extend_schema_view(
    put=extend_schema(
        tags=["Accounts"],
        summary="Replace the authenticated user profile",
        description=(
            "Update the current user profile. This endpoint supports `multipart/form-data` for avatar uploads. "
            "Avatar files are validated with a maximum size of 10 MB.\n\n"
            f"{AUTH_GUIDE}"
        ),
        request=ProfileUpdateSerializer,
        responses={
            200: success_response("ProfileUpdateResponse", ProfileSerializer),
            **standard_error_responses(400, 401, 500),
        },
        examples=[
            OpenApiExample(
                "ProfileUpdateRequest",
                value={
                    "headline": "Aspiring Frontend Engineer",
                    "bio": "Learning Django APIs and React integration.",
                    "country": "Nigeria",
                    "city": "Lagos",
                    "github": "https://github.com/aminayusuf",
                },
                request_only=True,
            )
        ],
    ),
    patch=extend_schema(
        tags=["Accounts"],
        summary="Partially update the authenticated user profile",
        description=(
            "Patch selected profile fields. Supports `multipart/form-data` for avatar upload and `application/json` for metadata-only updates.\n\n"
            f"{AUTH_GUIDE}"
        ),
        request=ProfileUpdateSerializer,
        responses={
            200: success_response("ProfilePartialUpdateResponse", ProfileSerializer),
            **standard_error_responses(400, 401, 500),
        },
    ),
)
class ProfileUpdateView(generics.UpdateAPIView):
    """PUT/PATCH /api/v1/auth/profile/update/"""

    serializer_class = ProfileUpdateSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

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


@extend_schema_view(
    put=extend_schema(
        tags=["Accounts"],
        summary="Change account password",
        description=(
            "Rotate the authenticated user's password. The current password must be supplied, and Django password validation rules apply to the new password.\n\n"
            f"{AUTH_GUIDE}"
        ),
        request=ChangePasswordSerializer,
        responses={
            200: success_response(
                "ChangePasswordResponse",
                MessageOnlySerializer,
                examples=[success_example("PasswordChanged", "Password changed successfully.", {})],
            ),
            **standard_error_responses(400, 401, 500),
        },
    )
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


@extend_schema(
    tags=["Accounts"],
    summary="List all platform users",
    description=f"Administrative user directory with pagination.\n\n{AUTH_GUIDE}\n\n{ROLE_ACCESS_GUIDE}",
    parameters=[PAGE_PARAM, PAGE_SIZE_PARAM],
    responses={
        200: paginated_response(
            "AdminUsersResponse",
            AdminUserSerializer,
            description="Paginated user directory.",
        ),
        **standard_error_responses(401, 403, 500),
    },
)
class AdminUsersView(BaseAdminUserListView):
    """GET /api/v1/admin/users/"""


@extend_schema(
    tags=["Accounts"],
    summary="List instructor accounts",
    description=f"Administrative instructor directory with pagination.\n\n{AUTH_GUIDE}\n\n{ROLE_ACCESS_GUIDE}",
    parameters=[PAGE_PARAM, PAGE_SIZE_PARAM],
    responses={
        200: paginated_response("AdminInstructorsResponse", AdminUserSerializer),
        **standard_error_responses(401, 403, 500),
    },
)
class AdminInstructorsView(BaseAdminUserListView):
    """GET /api/v1/admin/instructors/"""

    role_filter = User.Role.INSTRUCTOR


@extend_schema(
    tags=["Accounts"],
    summary="List student accounts",
    description=f"Administrative student directory with pagination.\n\n{AUTH_GUIDE}\n\n{ROLE_ACCESS_GUIDE}",
    parameters=[PAGE_PARAM, PAGE_SIZE_PARAM],
    responses={
        200: paginated_response("AdminStudentsResponse", AdminUserSerializer),
        **standard_error_responses(401, 403, 500),
    },
)
class AdminStudentsView(BaseAdminUserListView):
    """GET /api/v1/admin/students/"""

    role_filter = User.Role.STUDENT


@extend_schema_view(
    post=extend_schema(
        tags=["Accounts"],
        summary="Activate or deactivate a user account",
        description=(
            "Administrative endpoint used to toggle account status. "
            "Set `action` to `activate` or `deactivate`.\n\n"
            f"{AUTH_GUIDE}\n\n{ROLE_ACCESS_GUIDE}"
        ),
        parameters=[
            OpenApiParameter(
                name="user_id",
                type=OpenApiTypes.UUID,
                location=OpenApiParameter.PATH,
                description="Target user identifier.",
            ),
            UserStatusActionParameter,
        ],
        responses={
            200: success_response("AdminUserStatusResponse", AdminUserSerializer),
            **standard_error_responses(401, 403, 404, 500),
        },
        examples=[
            success_example(
                "DeactivateUser",
                "User deactivated successfully.",
                {**USER_EXAMPLE, "is_active": False},
            )
        ],
    )
)
class AdminUserStatusView(APIView):
    """POST /api/v1/admin/users/{user_id}/{action}/"""

    permission_classes = [IsAuthenticated, IsAdmin]

    @extend_schema(
        tags=["Accounts"],
        summary="Activate or deactivate user account",
        request=None,
        parameters=[
            OpenApiParameter(
                name="user_id",
                type=OpenApiTypes.UUID,
                location=OpenApiParameter.PATH,
                description="Target user identifier.",
            ),
            UserStatusActionParameter,
        ],
        responses={
            200: success_response("AdminUserStatusMethodResponse", AdminUserSerializer),
            **standard_error_responses(401, 403, 404, 500),
        },
    )
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
