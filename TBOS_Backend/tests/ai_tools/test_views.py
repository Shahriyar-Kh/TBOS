from unittest.mock import patch

import pytest

from tests.factories import CourseFactory


@pytest.mark.django_db
class TestAIToolsViews:
    @patch("apps.ai_tools.views.generate_ai_quiz.delay")
    def test_generate_quiz_queues_job(self, mocked_delay, instructor_client, instructor_user):
        course = CourseFactory(instructor=instructor_user)

        response = instructor_client.post(
            "/api/v1/ai/generate-quiz/",
            {"course_id": str(course.id), "prompt": "Create quiz", "num_questions": 5},
            format="json",
        )

        assert response.status_code == 202
        mocked_delay.assert_called_once()

    def test_generate_quiz_status_not_found_for_other_user(self, instructor_client):
        response = instructor_client.get("/api/v1/ai/generate-quiz/11111111-1111-1111-1111-111111111111/status/")
        assert response.status_code == 404

    @patch("apps.ai_tools.views.generate_ai_content_suggestion.delay")
    def test_suggest_queues_job(self, mocked_delay, instructor_client):
        response = instructor_client.post(
            "/api/v1/ai/suggest/",
            {"suggestion_type": "lesson_outline", "input_text": "Plan lesson"},
            format="json",
        )

        assert response.status_code == 202
        mocked_delay.assert_called_once()
