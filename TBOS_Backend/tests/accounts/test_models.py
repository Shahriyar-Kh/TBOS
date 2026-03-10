import pytest
from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.mark.django_db
class TestUserRegistration:
    def test_create_user(self):
        user = User.objects.create_user(
            email="test@example.com",
            password="securepass123",
            first_name="Test",
            last_name="User",
        )
        assert user.email == "test@example.com"
        assert user.role == "student"
        assert user.check_password("securepass123")
        assert hasattr(user, "profile")

    def test_create_superuser(self):
        admin = User.objects.create_superuser(
            email="super@example.com",
            password="adminpass123",
            first_name="Super",
            last_name="Admin",
        )
        assert admin.is_staff is True
        assert admin.is_superuser is True
        assert admin.role == "admin"
