import pytest


@pytest.mark.django_db
class TestLessonPermissions:
    def test_unauthorized_instructor_sections_returns_401(self, api_client):
        response = api_client.get("/api/v1/lessons/instructor/sections/")
        assert response.status_code == 401

    def test_student_cannot_access_instructor_sections(self, auth_client):
        response = auth_client.get("/api/v1/lessons/instructor/sections/")
        assert response.status_code == 403

    def test_instructor_can_access_instructor_sections(self, instructor_client):
        response = instructor_client.get("/api/v1/lessons/instructor/sections/")
        assert response.status_code == 200
