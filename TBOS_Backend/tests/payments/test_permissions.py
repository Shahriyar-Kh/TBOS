import pytest


@pytest.mark.django_db
class TestPaymentPermissions:
    def test_unauthorized_checkout_returns_401(self, api_client):
        response = api_client.post("/api/v1/payments/checkout/", {}, format="json")
        assert response.status_code == 401

    def test_instructor_cannot_checkout(self, instructor_client):
        response = instructor_client.post("/api/v1/payments/checkout/", {}, format="json")
        assert response.status_code == 403

    def test_student_cannot_access_admin_payments(self, auth_client):
        response = auth_client.get("/api/v1/admin/payments/")
        assert response.status_code == 403

    def test_admin_can_access_admin_payments(self, admin_client):
        response = admin_client.get("/api/v1/admin/payments/")
        assert response.status_code == 200
