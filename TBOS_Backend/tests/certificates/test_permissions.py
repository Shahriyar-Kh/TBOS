import pytest


@pytest.mark.django_db
class TestCertificatePermissions:
    def test_unauthorized_my_certificates_returns_401(self, api_client):
        response = api_client.get("/api/v1/certificates/my/")
        assert response.status_code == 401

    def test_instructor_cannot_access_student_certificate_list(self, instructor_client):
        response = instructor_client.get("/api/v1/certificates/my/")
        assert response.status_code == 403

    def test_student_can_access_own_certificates(self, auth_client):
        response = auth_client.get("/api/v1/certificates/my/")
        assert response.status_code == 200

    def test_public_verify_endpoint_accessible_without_auth(self, api_client):
        response = api_client.get("/api/v1/certificates/verify/not-a-real-code/")
        assert response.status_code == 404
