import pytest
from django.contrib.auth import get_user_model


User = get_user_model()


@pytest.mark.django_db
class TestCustomUserManager:
    def test_create_user_sets_defaults_and_normalizes_email(self):
        user = User.objects.create_user(
            email="MANAGER@Example.COM",
            password="StrongPass123!",
            first_name="Manager",
            last_name="User",
        )

        assert user.email == "manager@example.com"
        assert user.role == User.Role.STUDENT
        assert user.is_staff is False
        assert user.is_superuser is False

    def test_create_user_without_password_sets_unusable_password(self):
        user = User.objects.create_user(
            email="unusable@example.com",
            password=None,
            first_name="No",
            last_name="Password",
        )

        assert user.has_usable_password() is False

    def test_create_user_requires_email(self):
        with pytest.raises(ValueError, match="Email address is required"):
            User.objects.create_user(email="", password="StrongPass123!")

    def test_create_superuser_sets_required_flags(self):
        user = User.objects.create_superuser(
            email="admin-manager@example.com",
            password="StrongPass123!",
            first_name="Admin",
            last_name="Manager",
        )

        assert user.is_staff is True
        assert user.is_superuser is True
        assert user.is_verified is True
        assert user.role == User.Role.ADMIN

    def test_create_superuser_requires_staff(self):
        with pytest.raises(ValueError, match="is_staff=True"):
            User.objects.create_superuser(
                email="bad-admin1@example.com",
                password="StrongPass123!",
                is_staff=False,
            )

    def test_create_superuser_requires_superuser(self):
        with pytest.raises(ValueError, match="is_superuser=True"):
            User.objects.create_superuser(
                email="bad-admin2@example.com",
                password="StrongPass123!",
                is_superuser=False,
            )