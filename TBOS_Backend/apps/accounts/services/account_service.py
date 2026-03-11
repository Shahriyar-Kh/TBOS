from django.conf import settings
from django.contrib.auth import authenticate, get_user_model
from django.db import transaction
from rest_framework.exceptions import AuthenticationFailed, ValidationError
from rest_framework_simplejwt.tokens import RefreshToken

from apps.accounts.models import Profile
from apps.accounts.tasks import send_welcome_email

User = get_user_model()


class AccountService:
    @staticmethod
    def _build_auth_payload(user):
        refresh = RefreshToken.for_user(user)
        return {
            "access_token": str(refresh.access_token),
            "refresh_token": str(refresh),
            "user_role": user.role,
            "user": {
                "id": str(user.id),
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "role": user.role,
                "is_verified": user.is_verified,
                "google_account": user.google_account,
            },
        }

    @staticmethod
    def create_profile(user):
        profile, _ = Profile.objects.get_or_create(user=user)
        return profile

    @staticmethod
    def register_user(validated_data: dict):
        validated_data.pop("confirm_password", None)
        role = validated_data.get("role", User.Role.STUDENT)
        if role == User.Role.ADMIN:
            raise ValidationError({"role": "Admin accounts cannot be self-registered."})

        with transaction.atomic():
            user = User.objects.create_user(
                email=validated_data["email"],
                password=validated_data["password"],
                first_name=validated_data["first_name"],
                last_name=validated_data["last_name"],
                role=role,
                username=validated_data.get("username") or None,
                google_account=False,
                is_verified=False,
            )
            AccountService.create_profile(user)

        try:
            send_welcome_email.delay(str(user.id))
        except Exception:
            pass

        return user, AccountService._build_auth_payload(user)

    @staticmethod
    def login_user(email: str, password: str, request=None):
        user = authenticate(request=request, email=email, password=password)
        if not user:
            user = authenticate(request=request, username=email, password=password)

        if not user:
            raise AuthenticationFailed("Invalid email or password.")
        if not user.is_active:
            raise AuthenticationFailed("This account is inactive.")

        return AccountService._build_auth_payload(user)

    @staticmethod
    def update_profile(user, validated_data: dict):
        profile, _ = Profile.objects.get_or_create(user=user)
        for attr, value in validated_data.items():
            setattr(profile, attr, value)
        profile.save()
        return profile

    @staticmethod
    def change_password(user, new_password: str) -> None:
        user.set_password(new_password)
        user.save(update_fields=["password"])

    @staticmethod
    def handle_google_login(id_token: str):
        from allauth.socialaccount.models import SocialAccount
        from google.auth.transport.requests import Request
        from google.oauth2.id_token import verify_oauth2_token

        client_id = getattr(settings, "GOOGLE_OAUTH_CLIENT_ID", "")
        if not client_id:
            raise ValidationError({"id_token": "Google OAuth is not configured."})

        try:
            token_data = verify_oauth2_token(id_token, Request(), client_id)
        except Exception as exc:
            raise AuthenticationFailed("Invalid Google token.") from exc

        email = (token_data.get("email") or "").lower().strip()
        if not email:
            raise ValidationError({"id_token": "Google account email was not provided."})

        with transaction.atomic():
            user = User.objects.filter(email=email).first()
            created = False
            if not user:
                user = User.objects.create_user(
                    email=email,
                    password=None,
                    first_name=token_data.get("given_name", ""),
                    last_name=token_data.get("family_name", ""),
                    role=User.Role.STUDENT,
                    google_account=True,
                    is_verified=True,
                )
                created = True
            else:
                updated_fields = []
                if not user.google_account:
                    user.google_account = True
                    updated_fields.append("google_account")
                if not user.is_verified:
                    user.is_verified = True
                    updated_fields.append("is_verified")
                if updated_fields:
                    user.save(update_fields=updated_fields)

            AccountService.create_profile(user)
            SocialAccount.objects.update_or_create(
                user=user,
                provider="google",
                uid=token_data.get("sub", email),
                defaults={"extra_data": token_data},
            )

        if created:
            try:
                send_welcome_email.delay(str(user.id))
            except Exception:
                pass

        return created, AccountService._build_auth_payload(user)

    @staticmethod
    def logout_user(refresh_token: str):
        token = RefreshToken(refresh_token)
        token.blacklist()

    @staticmethod
    def get_users(role=None):
        queryset = User.objects.select_related("profile").order_by("-date_joined")
        if role:
            queryset = queryset.filter(role=role)
        return queryset

    @staticmethod
    def deactivate_user(user) -> None:
        user.is_active = False
        user.save(update_fields=["is_active"])

    @staticmethod
    def activate_user(user) -> None:
        user.is_active = True
        user.save(update_fields=["is_active"])
