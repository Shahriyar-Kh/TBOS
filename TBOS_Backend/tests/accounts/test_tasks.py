from unittest.mock import patch

import pytest

from apps.accounts.tasks import (
    send_password_reset_email,
    send_verification_email,
    send_welcome_email,
)
from tests.factories import UserFactory


@pytest.mark.django_db
class TestAccountTasks:
    @patch("apps.accounts.tasks._send_email")
    def test_send_welcome_email_sends_message(self, mocked_send):
        user = UserFactory(first_name="Welcome", email="welcome@example.com")

        send_welcome_email.run(str(user.id))

        mocked_send.assert_called_once()
        _, kwargs = mocked_send.call_args
        assert kwargs["recipient_email"] == user.email

    @patch("apps.accounts.tasks._send_email")
    def test_send_welcome_email_ignores_missing_user(self, mocked_send):
        send_welcome_email.run("00000000-0000-0000-0000-000000000000")

        mocked_send.assert_not_called()

    @patch.object(send_welcome_email, "retry", side_effect=RuntimeError("retrying welcome"))
    @patch("apps.accounts.tasks._send_email", side_effect=RuntimeError("boom"))
    def test_send_welcome_email_retries_on_failure(self, mocked_send, mocked_retry):
        user = UserFactory()

        with pytest.raises(RuntimeError, match="retrying welcome"):
            send_welcome_email.run(str(user.id))

        mocked_retry.assert_called_once()

    @patch("apps.accounts.tasks._send_email")
    def test_send_verification_email_sends_message(self, mocked_send):
        user = UserFactory(first_name="Verify", email="verify@example.com")

        send_verification_email.run(str(user.id), "https://example.com/verify")

        mocked_send.assert_called_once()

    @patch("apps.accounts.tasks._send_email")
    def test_send_verification_email_ignores_missing_user(self, mocked_send):
        send_verification_email.run(
            "00000000-0000-0000-0000-000000000000",
            "https://example.com/verify",
        )

        mocked_send.assert_not_called()

    @patch.object(send_verification_email, "retry", side_effect=RuntimeError("retrying verification"))
    @patch("apps.accounts.tasks._send_email", side_effect=RuntimeError("boom"))
    def test_send_verification_email_retries_on_failure(self, mocked_send, mocked_retry):
        user = UserFactory()

        with pytest.raises(RuntimeError, match="retrying verification"):
            send_verification_email.run(str(user.id), "https://example.com/verify")

        mocked_retry.assert_called_once()

    @patch("apps.accounts.tasks._send_email")
    def test_send_password_reset_email_sends_message(self, mocked_send):
        user = UserFactory(first_name="Reset", email="reset@example.com")

        send_password_reset_email.run(str(user.id), "https://example.com/reset")

        mocked_send.assert_called_once()

    @patch("apps.accounts.tasks._send_email")
    def test_send_password_reset_email_ignores_missing_user(self, mocked_send):
        send_password_reset_email.run(
            "00000000-0000-0000-0000-000000000000",
            "https://example.com/reset",
        )

        mocked_send.assert_not_called()

    @patch.object(send_password_reset_email, "retry", side_effect=RuntimeError("retrying reset"))
    @patch("apps.accounts.tasks._send_email", side_effect=RuntimeError("boom"))
    def test_send_password_reset_email_retries_on_failure(self, mocked_send, mocked_retry):
        user = UserFactory()

        with pytest.raises(RuntimeError, match="retrying reset"):
            send_password_reset_email.run(str(user.id), "https://example.com/reset")

        mocked_retry.assert_called_once()