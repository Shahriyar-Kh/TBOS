from unittest.mock import patch

import pytest
from rest_framework.exceptions import AuthenticationFailed, ValidationError
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken
from rest_framework_simplejwt.tokens import AccessToken, RefreshToken

from apps.accounts.models import User
from apps.accounts.services.account_service import AccountService
from tests.factories import UserFactory


@pytest.mark.django_db
class TestAccountService:
    @patch("apps.accounts.services.account_service.send_welcome_email.delay")
    def test_register_user_creates_records(self, mocked_delay):
        user, payload = AccountService.register_user(
            {
                "first_name": "Test",
                "last_name": "User",
                "email": "service-register@example.com",
                "password": "StrongPass123!",
                "confirm_password": "StrongPass123!",
                "role": User.Role.STUDENT,
            }
        )

        assert user.email == "service-register@example.com"
        assert user.profile is not None
        assert payload["user_role"] == User.Role.STUDENT
        assert "access_token" in payload
        mocked_delay.assert_called_once()

    def test_register_user_rejects_admin_self_registration(self):
        with pytest.raises(ValidationError):
            AccountService.register_user(
                {
                    "first_name": "Admin",
                    "last_name": "User",
                    "email": "admin-register@example.com",
                    "password": "StrongPass123!",
                    "confirm_password": "StrongPass123!",
                    "role": User.Role.ADMIN,
                }
            )

    @patch("apps.accounts.services.account_service.send_welcome_email.delay", side_effect=RuntimeError("queue unavailable"))
    def test_register_user_ignores_welcome_email_failures(self, mocked_delay):
        user, payload = AccountService.register_user(
            {
                "first_name": "Grace",
                "last_name": "Hopper",
                "email": "grace@example.com",
                "password": "StrongPass123!",
                "confirm_password": "StrongPass123!",
                "role": User.Role.STUDENT,
            }
        )

        assert user.email == "grace@example.com"
        assert payload["user_role"] == User.Role.STUDENT
        mocked_delay.assert_called_once()

    def test_login_user_returns_valid_tokens(self):
        user = UserFactory(email="login-service@example.com")

        payload = AccountService.login_user(user.email, "StrongPass123!")

        assert payload["user"]["email"] == user.email
        assert str(AccessToken(payload["access_token"]))
        assert str(RefreshToken(payload["refresh_token"]))

    def test_login_user_raises_for_invalid_credentials(self):
        UserFactory(email="invalid-login@example.com")

        with pytest.raises(AuthenticationFailed):
            AccountService.login_user("invalid-login@example.com", "WrongPass123!")

    @patch("apps.accounts.services.account_service.authenticate")
    def test_login_user_raises_for_inactive_account(self, mocked_authenticate):
        user = UserFactory(email="inactive@example.com", is_active=False)
        mocked_authenticate.return_value = user

        with pytest.raises(AuthenticationFailed, match="inactive"):
            AccountService.login_user(user.email, "StrongPass123!")

    def test_update_profile_updates_profile_fields(self):
        user = UserFactory()

        profile = AccountService.update_profile(
            user,
            {
                "bio": "Updated through service",
                "skills": ["Django", "Celery"],
                "linkedin": "https://linkedin.com/in/service-user",
            },
        )

        assert profile.bio == "Updated through service"
        assert profile.skills == ["Django", "Celery"]

    def test_create_profile_returns_existing_profile(self):
        user = UserFactory()

        profile = AccountService.create_profile(user)

        assert profile.id == user.profile.id

    @patch("apps.accounts.services.account_service.send_welcome_email.delay")
    @patch("google.oauth2.id_token.verify_oauth2_token")
    def test_handle_google_login_creates_new_google_user(self, mocked_verify, mocked_delay, settings):
        mocked_verify.return_value = {
            "sub": "google-sub-1",
            "email": "google-new@example.com",
            "given_name": "Google",
            "family_name": "User",
        }
        settings.GOOGLE_OAUTH_CLIENT_ID = "test-google-client-id"

        created, payload = AccountService.handle_google_login("fake-token")

        assert created is True
        assert payload["user"]["email"] == "google-new@example.com"
        assert payload["user"]["role"] == User.Role.STUDENT
        assert payload["user"]["google_account"] is True
        mocked_delay.assert_called_once()

    @patch("apps.accounts.services.account_service.send_welcome_email.delay")
    @patch("google.oauth2.id_token.verify_oauth2_token")
    def test_handle_google_login_updates_existing_user(self, mocked_verify, mocked_delay, settings):
        user = UserFactory(email="google-existing@example.com", google_account=False, is_verified=False)
        mocked_verify.return_value = {
            "sub": "google-sub-existing",
            "email": user.email,
            "given_name": user.first_name,
            "family_name": user.last_name,
        }
        settings.GOOGLE_OAUTH_CLIENT_ID = "test-google-client-id"

        created, payload = AccountService.handle_google_login("fake-token")
        user.refresh_from_db()

        assert created is False
        assert user.google_account is True
        assert user.is_verified is True
        assert payload["user_role"] == User.Role.STUDENT
        mocked_delay.assert_not_called()

    def test_handle_google_login_requires_configured_client_id(self, settings):
        settings.GOOGLE_OAUTH_CLIENT_ID = ""

        with pytest.raises(ValidationError):
            AccountService.handle_google_login("fake-token")

    @patch("google.oauth2.id_token.verify_oauth2_token", side_effect=ValueError("invalid"))
    def test_handle_google_login_rejects_invalid_token(self, mocked_verify, settings):
        settings.GOOGLE_OAUTH_CLIENT_ID = "test-google-client-id"

        with pytest.raises(AuthenticationFailed, match="Invalid Google token"):
            AccountService.handle_google_login("fake-token")

    @patch("google.oauth2.id_token.verify_oauth2_token")
    def test_handle_google_login_requires_email(self, mocked_verify, settings):
        mocked_verify.return_value = {"sub": "google-sub-without-email"}
        settings.GOOGLE_OAUTH_CLIENT_ID = "test-google-client-id"

        with pytest.raises(ValidationError):
            AccountService.handle_google_login("fake-token")

    def test_logout_user_blacklists_refresh_token(self):
        user = UserFactory()
        refresh = RefreshToken.for_user(user)

        AccountService.logout_user(str(refresh))

        assert BlacklistedToken.objects.filter(token__jti=refresh["jti"]).exists()

    def test_get_users_filters_by_role(self):
        student = UserFactory(email="student-filter@example.com")
        instructor = UserFactory(
            email="instructor-filter@example.com",
            role=User.Role.INSTRUCTOR,
            username="instructor-filter",
        )

        filtered = AccountService.get_users(role=User.Role.INSTRUCTOR)

        assert instructor in filtered
        assert student not in filtered

    def test_activate_and_deactivate_user(self):
        user = UserFactory()

        AccountService.deactivate_user(user)
        user.refresh_from_db()
        assert user.is_active is False

        AccountService.activate_user(user)
        user.refresh_from_db()
        assert user.is_active is True