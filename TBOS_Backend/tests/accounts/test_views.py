from datetime import timedelta
from unittest.mock import patch

import pytest
from rest_framework import status
from rest_framework_simplejwt.tokens import AccessToken, RefreshToken


def assert_standard_response(payload, success):
    assert payload["success"] is success
    assert "message" in payload
    if success:
        assert "data" in payload
    else:
        assert "errors" in payload


def assert_no_password_exposed(payload):
    if isinstance(payload, dict):
        assert "password" not in payload
        for value in payload.values():
            assert_no_password_exposed(value)
    elif isinstance(payload, list):
        for item in payload:
            assert_no_password_exposed(item)


@pytest.mark.django_db
class TestRegistrationAPI:
    @patch("apps.accounts.services.account_service.send_welcome_email.delay")
    def test_user_registers_successfully(self, mocked_delay, api_client):
        response = api_client.post(
            "/api/v1/auth/register/",
            {
                "first_name": "New",
                "last_name": "User",
                "email": "register@example.com",
                "password": "StrongPass123!",
                "confirm_password": "StrongPass123!",
                "role": "student",
            },
            format="json",
        )

        assert response.status_code == status.HTTP_201_CREATED
        assert_standard_response(response.data, True)
        assert response.data["data"]["user_role"] == "student"
        assert response.data["data"]["user"]["email"] == "register@example.com"
        assert_no_password_exposed(response.data)
        mocked_delay.assert_called_once()

    def test_registration_fails_if_email_exists(self, api_client, student_user):
        response = api_client.post(
            "/api/v1/auth/register/",
            {
                "first_name": "New",
                "last_name": "User",
                "email": student_user.email,
                "password": "StrongPass123!",
                "confirm_password": "StrongPass123!",
            },
            format="json",
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert_standard_response(response.data, False)

    def test_registration_fails_password_mismatch(self, api_client):
        response = api_client.post(
            "/api/v1/auth/register/",
            {
                "first_name": "New",
                "last_name": "User",
                "email": "mismatch@example.com",
                "password": "StrongPass123!",
                "confirm_password": "WrongPass123!",
            },
            format="json",
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert_standard_response(response.data, False)

    def test_registration_enforces_password_validation(self, api_client):
        response = api_client.post(
            "/api/v1/auth/register/",
            {
                "first_name": "Weak",
                "last_name": "Password",
                "email": "weak@example.com",
                "password": "123",
                "confirm_password": "123",
            },
            format="json",
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert_standard_response(response.data, False)

    def test_profile_automatically_created_after_registration(self, api_client):
        response = api_client.post(
            "/api/v1/auth/register/",
            {
                "first_name": "Profile",
                "last_name": "Created",
                "email": "profile-created@example.com",
                "password": "StrongPass123!",
                "confirm_password": "StrongPass123!",
            },
            format="json",
        )

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["data"]["user"]["profile"]["id"] is not None


@pytest.mark.django_db
class TestLoginAPI:
    def test_login_with_correct_credentials(self, api_client, student_user):
        response = api_client.post(
            "/api/v1/auth/login/",
            {"email": student_user.email, "password": "StrongPass123!"},
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK
        assert_standard_response(response.data, True)
        assert response.data["data"]["user_role"] == student_user.role
        assert str(AccessToken(response.data["data"]["access_token"]))
        assert str(RefreshToken(response.data["data"]["refresh_token"]))
        assert_no_password_exposed(response.data)

    def test_login_fails_with_incorrect_password(self, api_client, student_user):
        response = api_client.post(
            "/api/v1/auth/login/",
            {"email": student_user.email, "password": "WrongPass123!"},
            format="json",
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert_standard_response(response.data, False)

    def test_login_fails_with_non_existing_email(self, api_client):
        response = api_client.post(
            "/api/v1/auth/login/",
            {"email": "missing@example.com", "password": "StrongPass123!"},
            format="json",
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert_standard_response(response.data, False)

    def test_login_rate_limiting_triggers_after_multiple_failures(self, api_client):
        for _ in range(10):
            response = api_client.post(
                "/api/v1/auth/login/",
                {"email": "missing@example.com", "password": "WrongPass123!"},
                format="json",
                REMOTE_ADDR="127.0.0.55",
            )
            assert response.status_code == status.HTTP_401_UNAUTHORIZED

        blocked = api_client.post(
            "/api/v1/auth/login/",
            {"email": "missing@example.com", "password": "WrongPass123!"},
            format="json",
            REMOTE_ADDR="127.0.0.55",
        )

        assert blocked.status_code in {
            status.HTTP_403_FORBIDDEN,
            status.HTTP_429_TOO_MANY_REQUESTS,
        }


@pytest.mark.django_db
class TestGoogleLoginAPI:
    @patch("apps.accounts.views.AccountService.handle_google_login")
    def test_new_google_user_account_created(self, mocked_handle, api_client):
        mocked_handle.return_value = (
            True,
            {
                "access_token": "mock-access-token",
                "refresh_token": "mock-refresh-token",
                "user_role": "student",
                "user": {
                    "id": "123",
                    "email": "google-new@example.com",
                    "role": "student",
                    "google_account": True,
                },
            },
        )

        response = api_client.post(
            "/api/v1/auth/google-login/",
            {"id_token": "fake-google-id-token"},
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data["data"]["user_role"] == "student"
        assert response.data["data"]["user"]["google_account"] is True

    @patch("apps.accounts.views.AccountService.handle_google_login")
    def test_existing_google_user_logs_in_successfully(self, mocked_handle, api_client):
        mocked_handle.return_value = (
            False,
            {
                "access_token": "mock-access-token",
                "refresh_token": "mock-refresh-token",
                "user_role": "student",
                "user": {
                    "id": "123",
                    "email": "google-existing@example.com",
                    "role": "student",
                    "google_account": True,
                },
            },
        )

        response = api_client.post(
            "/api/v1/auth/google-login/",
            {"id_token": "fake-google-id-token"},
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data["data"]["user"]["email"] == "google-existing@example.com"


@pytest.mark.django_db
class TestProfileAPI:
    def test_authenticated_user_can_view_profile(self, auth_client):
        response = auth_client.get("/api/v1/auth/profile/")

        assert response.status_code == status.HTTP_200_OK
        assert_standard_response(response.data, True)

    def test_unauthenticated_profile_request_denied(self, api_client):
        response = api_client.get("/api/v1/auth/profile/")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_profile_update_avatar_success(self, auth_client, avatar_file):
        response = auth_client.put(
            "/api/v1/auth/profile/update/",
            {"avatar": avatar_file},
            format="multipart",
        )

        assert response.status_code == status.HTTP_200_OK
        assert_standard_response(response.data, True)
        assert response.data["data"]["avatar"]

    def test_profile_update_bio_social_links_and_skills(self, auth_client):
        response = auth_client.put(
            "/api/v1/auth/profile/update/",
            {
                "bio": "Updated biography",
                "headline": "Senior Instructor",
                "linkedin": "https://linkedin.com/in/tbos-user",
                "github": "https://github.com/tbos-user",
                "twitter": "https://twitter.com/tbos_user",
                "skills": ["Django", "DRF", "Celery"],
            },
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data["data"]["bio"] == "Updated biography"
        assert response.data["data"]["skills"] == ["Django", "DRF", "Celery"]

    def test_profile_update_rejects_invalid_social_link(self, auth_client):
        response = auth_client.put(
            "/api/v1/auth/profile/update/",
            {"linkedin": "not-a-valid-url"},
            format="json",
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert_standard_response(response.data, False)

    def test_profile_update_rejects_large_avatar(self, auth_client, large_avatar_file):
        response = auth_client.put(
            "/api/v1/auth/profile/update/",
            {"avatar": large_avatar_file},
            format="multipart",
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert_standard_response(response.data, False)

    def test_profile_update_rejects_invalid_phone_number(self, auth_client):
        response = auth_client.put(
            "/api/v1/auth/profile/update/",
            {"phone_number": "abc-123"},
            format="json",
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert_standard_response(response.data, False)

    def test_me_returns_authenticated_user_details(self, auth_client, student_user):
        response = auth_client.get("/api/v1/auth/me/")

        assert response.status_code == status.HTTP_200_OK
        assert response.data["data"]["email"] == student_user.email

    def test_change_password_updates_credentials(self, auth_client, student_user):
        response = auth_client.put(
            "/api/v1/auth/change-password/",
            {
                "old_password": "StrongPass123!",
                "new_password": "EvenStrongerPass123!",
            },
            format="json",
        )

        student_user.refresh_from_db()

        assert response.status_code == status.HTTP_200_OK
        assert student_user.check_password("EvenStrongerPass123!") is True

    def test_change_password_rejects_wrong_old_password(self, auth_client):
        response = auth_client.put(
            "/api/v1/auth/change-password/",
            {
                "old_password": "WrongPass123!",
                "new_password": "EvenStrongerPass123!",
            },
            format="json",
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert_standard_response(response.data, False)

    def test_logout_blacklists_refresh_token(self, api_client, student_user, access_token_for_user):
        refresh_token = str(RefreshToken.for_user(student_user))
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token_for_user(student_user)}")

        response = api_client.post(
            "/api/v1/auth/logout/",
            {"refresh_token": refresh_token},
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK
        assert_standard_response(response.data, True)


@pytest.mark.django_db
class TestRoleBasedAccessAndJWT:
    def test_admin_can_access_admin_api(self, admin_client):
        response = admin_client.get("/api/v1/admin/users/")

        assert response.status_code == status.HTTP_200_OK
        assert_standard_response(response.data, True)

    def test_instructor_cannot_access_admin_api(self, instructor_client):
        response = instructor_client.get("/api/v1/admin/users/")

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_student_cannot_access_admin_api(self, auth_client):
        response = auth_client.get("/api/v1/admin/users/")

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_access_protected_endpoint_with_valid_token(self, api_client, student_user):
        token = str(RefreshToken.for_user(student_user).access_token)
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

        response = api_client.get("/api/v1/auth/profile/")

        assert response.status_code == status.HTTP_200_OK

    def test_access_protected_endpoint_without_token(self, api_client):
        response = api_client.get("/api/v1/auth/profile/")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_access_protected_endpoint_with_expired_token(self, api_client, student_user):
        token = RefreshToken.for_user(student_user).access_token
        token.set_exp(lifetime=timedelta(seconds=-1))
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {str(token)}")

        response = api_client.get("/api/v1/auth/profile/")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_sensitive_fields_not_exposed_in_me_response(self, auth_client):
        response = auth_client.get("/api/v1/auth/me/")

        assert response.status_code == status.HTTP_200_OK
        assert_no_password_exposed(response.data)

    def test_admin_can_filter_instructors(self, admin_client, instructor_user):
        response = admin_client.get("/api/v1/admin/instructors/")

        assert response.status_code == status.HTTP_200_OK
        assert any(result["id"] == str(instructor_user.id) for result in response.data["data"]["results"])

    def test_admin_can_filter_students(self, admin_client, student_user):
        response = admin_client.get("/api/v1/admin/students/")

        assert response.status_code == status.HTTP_200_OK
        assert any(result["id"] == str(student_user.id) for result in response.data["data"]["results"])

    def test_admin_can_deactivate_user(self, admin_client, student_user):
        response = admin_client.post(f"/api/v1/admin/users/{student_user.id}/deactivate/")
        student_user.refresh_from_db()

        assert response.status_code == status.HTTP_200_OK
        assert student_user.is_active is False

    def test_admin_can_activate_user(self, admin_client, student_user):
        student_user.is_active = False
        student_user.save(update_fields=["is_active"])

        response = admin_client.post(f"/api/v1/admin/users/{student_user.id}/activate/")
        student_user.refresh_from_db()

        assert response.status_code == status.HTTP_200_OK
        assert student_user.is_active is True
