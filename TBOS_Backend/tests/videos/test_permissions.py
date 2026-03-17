import pytest


@pytest.mark.django_db
class TestVideoPermissions:
    def test_unauthorized_instructor_videos_returns_401(self, api_client):
        response = api_client.get("/api/v1/videos/instructor/")
        assert response.status_code == 401

    def test_student_cannot_access_instructor_video_endpoint(self, auth_client):
        response = auth_client.get("/api/v1/videos/instructor/")
        assert response.status_code == 403

    def test_instructor_can_access_instructor_video_endpoint(self, instructor_client):
        response = instructor_client.get("/api/v1/videos/instructor/")
        assert response.status_code == 200
