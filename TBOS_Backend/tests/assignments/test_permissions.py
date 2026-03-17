import pytest


@pytest.mark.django_db
class TestAssignmentPermissions:
    def test_unauthorized_student_assignment_endpoint_returns_401(self, api_client):
        response = api_client.get("/api/v1/assignments/student/")
        assert response.status_code == 401

    def test_student_cannot_access_instructor_assignment_endpoint(self, auth_client):
        response = auth_client.get("/api/v1/assignments/instructor/")
        assert response.status_code == 403

    def test_instructor_can_access_instructor_assignment_endpoint(self, instructor_client):
        response = instructor_client.get("/api/v1/assignments/instructor/")
        assert response.status_code == 200

    def test_instructor_cannot_access_admin_payments_endpoint(self, instructor_client):
        response = instructor_client.get("/api/v1/admin/payments/")
        assert response.status_code == 403
