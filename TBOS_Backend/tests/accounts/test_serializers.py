import pytest
from rest_framework.test import APIRequestFactory

from apps.accounts.serializers import (
    AdminUserSerializer,
    ChangePasswordSerializer,
    LoginSerializer,
    ProfileUpdateSerializer,
    RegisterSerializer,
    UserSerializer,
)
from tests.factories import UserFactory


@pytest.mark.django_db
class TestRegisterSerializer:
    def test_register_serializer_valid_data(self):
        serializer = RegisterSerializer(
            data={
                "first_name": "Alice",
                "last_name": "Doe",
                "email": "alice@example.com",
                "password": "StrongPass123!",
                "confirm_password": "StrongPass123!",
                "role": "student",
            }
        )

        assert serializer.is_valid(), serializer.errors

    def test_register_serializer_rejects_duplicate_email(self):
        UserFactory(email="duplicate@example.com")
        serializer = RegisterSerializer(
            data={
                "first_name": "Alice",
                "last_name": "Doe",
                "email": "duplicate@example.com",
                "password": "StrongPass123!",
                "confirm_password": "StrongPass123!",
            }
        )

        assert serializer.is_valid() is False
        assert "email" in serializer.errors

    def test_register_serializer_rejects_password_mismatch(self):
        serializer = RegisterSerializer(
            data={
                "first_name": "Alice",
                "last_name": "Doe",
                "email": "alice2@example.com",
                "password": "StrongPass123!",
                "confirm_password": "Mismatch123!",
            }
        )

        assert serializer.is_valid() is False
        assert "confirm_password" in serializer.errors

    def test_register_serializer_rejects_duplicate_username(self):
        UserFactory(username="taken-username")
        serializer = RegisterSerializer(
            data={
                "first_name": "Alice",
                "last_name": "Doe",
                "email": "unique@example.com",
                "username": "taken-username",
                "password": "StrongPass123!",
                "confirm_password": "StrongPass123!",
            }
        )

        assert serializer.is_valid() is False
        assert "username" in serializer.errors

    def test_register_serializer_normalizes_email_and_username(self):
        serializer = RegisterSerializer(
            data={
                "first_name": "Alice",
                "last_name": "Doe",
                "email": "Alice@Example.COM ",
                "username": "  spaced-user  ",
                "password": "StrongPass123!",
                "confirm_password": "StrongPass123!",
            }
        )

        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data["email"] == "alice@example.com"
        assert serializer.validated_data["username"] == "spaced-user"


@pytest.mark.django_db
class TestLoginSerializer:
    def test_login_serializer_valid(self):
        serializer = LoginSerializer(
            data={"email": "login@example.com", "password": "StrongPass123!"}
        )

        assert serializer.is_valid(), serializer.errors


@pytest.mark.django_db
class TestProfileUpdateSerializer:
    def test_profile_update_accepts_valid_links_and_skills(self):
        serializer = ProfileUpdateSerializer(
            data={
                "bio": "Senior Django engineer",
                "linkedin": "https://linkedin.com/in/test-user",
                "github": "https://github.com/test-user",
                "skills": ["Django", "DRF", "PostgreSQL"],
                "phone_number": "+12345678901",
            }
        )

        assert serializer.is_valid(), serializer.errors

    def test_profile_update_rejects_invalid_url(self):
        serializer = ProfileUpdateSerializer(data={"linkedin": "invalid-url"})

        assert serializer.is_valid() is False
        assert "linkedin" in serializer.errors

    def test_profile_update_rejects_large_avatar(self, large_avatar_file):
        serializer = ProfileUpdateSerializer(data={"avatar": large_avatar_file})

        assert serializer.is_valid() is False
        assert "avatar" in serializer.errors

    def test_profile_update_rejects_invalid_phone_number(self):
        serializer = ProfileUpdateSerializer(data={"phone_number": "abc-123"})

        assert serializer.is_valid() is False
        assert "phone_number" in serializer.errors


@pytest.mark.django_db
class TestUserAndPasswordSerializers:
    def test_change_password_serializer_accepts_correct_old_password(self):
        user = UserFactory()
        request = APIRequestFactory().post("/api/v1/auth/change-password/")
        request.user = user
        serializer = ChangePasswordSerializer(
            data={
                "old_password": "StrongPass123!",
                "new_password": "StrongPass456!",
            },
            context={"request": request},
        )

        assert serializer.is_valid(), serializer.errors

    def test_change_password_serializer_rejects_wrong_old_password(self):
        user = UserFactory()
        request = APIRequestFactory().post("/api/v1/auth/change-password/")
        request.user = user
        serializer = ChangePasswordSerializer(
            data={
                "old_password": "WrongPass123!",
                "new_password": "StrongPass456!",
            },
            context={"request": request},
        )

        assert serializer.is_valid() is False
        assert "old_password" in serializer.errors

    def test_user_serializer_includes_profile(self):
        user = UserFactory()
        data = UserSerializer(user).data

        assert data["email"] == user.email
        assert data["profile"]["id"] == str(user.profile.id)

    def test_admin_user_serializer_exposes_admin_fields(self):
        user = UserFactory(is_verified=True)
        data = AdminUserSerializer(user).data

        assert data["is_verified"] is True
        assert data["is_active"] is True