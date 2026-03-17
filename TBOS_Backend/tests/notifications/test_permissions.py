import pytest


@pytest.mark.django_db
class TestNotificationPermissions:
    def test_unauthorized_notification_list_returns_401(self, api_client):
        response = api_client.get("/api/v1/notifications/")
        assert response.status_code == 401

    def test_student_can_access_own_notifications(self, auth_client):
        response = auth_client.get("/api/v1/notifications/")
        assert response.status_code == 200

    def test_student_cannot_access_admin_broadcast(self, auth_client):
        response = auth_client.post(
            "/api/v1/admin/notifications/broadcast/",
            {"title": "Notice", "message": "Hello"},
            format="json",
        )
        assert response.status_code == 403

    def test_admin_can_access_broadcast(self, admin_client):
        response = admin_client.post(
            "/api/v1/admin/notifications/broadcast/",
            {"title": "Notice", "message": "Hello"},
            format="json",
        )
        assert response.status_code == 202
