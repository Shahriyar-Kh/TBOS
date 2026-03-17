import pytest


@pytest.mark.django_db
class TestAIToolsPermissions:
    def test_unauthorized_generate_quiz_returns_401(self, api_client):
        response = api_client.post("/api/v1/ai/generate-quiz/", {}, format="json")
        assert response.status_code == 401

    def test_student_cannot_access_ai_tools(self, auth_client):
        response = auth_client.get("/api/v1/ai/suggestions/")
        assert response.status_code == 403

    def test_instructor_can_access_ai_suggestions_history(self, instructor_client):
        response = instructor_client.get("/api/v1/ai/suggestions/")
        assert response.status_code == 200

    def test_admin_can_access_ai_suggestions_history(self, admin_client):
        response = admin_client.get("/api/v1/ai/suggestions/")
        assert response.status_code == 200
