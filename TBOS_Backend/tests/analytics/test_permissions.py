import pytest


@pytest.mark.django_db
class TestAnalyticsPermissions:
    def test_unauthorized_student_dashboard_returns_401(self, api_client):
        response = api_client.get("/api/v1/analytics/student/dashboard/")
        assert response.status_code == 401

    def test_student_cannot_access_admin_dashboard(self, auth_client):
        response = auth_client.get("/api/v1/analytics/admin/dashboard/")
        assert response.status_code == 403

    def test_instructor_cannot_access_admin_dashboard(self, instructor_client):
        response = instructor_client.get("/api/v1/analytics/admin/dashboard/")
        assert response.status_code == 403

    def test_admin_can_access_admin_dashboard(self, admin_client):
        response = admin_client.get("/api/v1/analytics/admin/dashboard/")
        assert response.status_code == 200
