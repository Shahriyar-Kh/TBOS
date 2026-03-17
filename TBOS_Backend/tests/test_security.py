from unittest.mock import patch

import pytest

from tests.factories import CourseFactory, OrderFactory, UserFactory


@pytest.mark.django_db
class TestSecurity:
    def test_jwt_required_for_protected_profile_endpoint(self, api_client):
        response = api_client.get("/api/v1/auth/profile/")
        assert response.status_code == 401

    def test_password_is_not_returned_in_login_response(self, api_client):
        email = "secure-user@example.com"
        password = "StrongPass123!"
        UserFactory(email=email, username="secure-user", password=password)

        response = api_client.post(
            "/api/v1/auth/login/",
            {"email": email, "password": password},
            format="json",
        )
        assert response.status_code == 200
        payload = response.data.get("data", {})
        assert "password" not in str(payload).lower()

    def test_student_cannot_view_another_students_order(self, api_client, access_token_for_user):
        owner = UserFactory()
        other = UserFactory()
        order = OrderFactory(student=owner)

        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token_for_user(other)}")
        response = api_client.get(f"/api/v1/payments/order/{order.id}/")
        assert response.status_code == 404

    @patch("apps.payments.services.payment_service.stripe.PaymentIntent.retrieve")
    def test_payment_verification_cannot_be_spoofed_with_mismatched_metadata(
        self,
        mocked_retrieve,
        api_client,
        access_token_for_user,
    ):
        student = UserFactory()
        order = OrderFactory(student=student)
        other_order = OrderFactory(student=student, course=CourseFactory())

        mocked_retrieve.return_value = {
            "status": "succeeded",
            "metadata": {"order_id": str(other_order.id)},
            "amount_received": int(order.amount * 100),
        }

        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token_for_user(student)}")
        response = api_client.post(
            "/api/v1/payments/verify/",
            {"order_id": str(order.id), "transaction_id": "pi_fake"},
            format="json",
        )
        assert response.status_code == 400
