import pytest


@pytest.mark.django_db
class TestEnrollmentPermissions:
    def test_unauthorized_student_enrollments_returns_401(self, api_client):
        response = api_client.get("/api/v1/enrollments/student/")
        assert response.status_code == 401

    def test_student_cannot_access_admin_enrollments(self, auth_client):
        response = auth_client.get("/api/v1/enrollments/admin/")
        assert response.status_code == 403

    def test_instructor_cannot_access_student_enrollments(self, instructor_client):
        response = instructor_client.get("/api/v1/enrollments/student/")
        assert response.status_code == 403

    def test_admin_can_access_admin_enrollments(self, admin_client):
        response = admin_client.get("/api/v1/enrollments/admin/")
        assert response.status_code == 200
