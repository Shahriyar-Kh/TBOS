import pytest


@pytest.mark.django_db
class TestQuizPermissions:
    def test_unauthorized_student_quiz_endpoint_returns_401(self, api_client):
        response = api_client.get("/api/v1/quiz/student/")
        assert response.status_code == 401

    def test_student_cannot_access_instructor_quiz_endpoint(self, auth_client):
        response = auth_client.get("/api/v1/quiz/instructor/quizzes/")
        assert response.status_code == 403

    def test_instructor_cannot_access_admin_quiz_endpoint(self, instructor_client):
        response = instructor_client.get("/api/v1/quiz/admin/quizzes/")
        assert response.status_code == 403

    def test_admin_can_access_admin_quiz_endpoint(self, admin_client):
        response = admin_client.get("/api/v1/quiz/admin/quizzes/")
        assert response.status_code == 200
