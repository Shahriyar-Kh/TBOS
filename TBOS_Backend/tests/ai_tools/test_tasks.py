from unittest.mock import patch

import pytest

from apps.ai_tools.models import AIContentSuggestion, AIQuizGeneration
from apps.ai_tools.tasks import generate_ai_content_suggestion, generate_ai_quiz
from tests.factories import CourseFactory, InstructorFactory


@pytest.mark.django_db
class TestAIToolsTasks:
    def test_generate_ai_quiz_marks_processing_then_completed_placeholder(self):
        user = InstructorFactory()
        course = CourseFactory(instructor=user)
        job = AIQuizGeneration.objects.create(course=course, prompt="Q", initiated_by=user)

        generate_ai_quiz.run(str(job.id))

        job.refresh_from_db()
        assert job.status == AIQuizGeneration.Status.COMPLETED
        assert "not configured" in job.error_message.lower()

    @patch("apps.ai_tools.tasks.generate_ai_quiz.retry", side_effect=RuntimeError("retry"))
    def test_generate_ai_quiz_retries_on_error(self, _mocked_retry):
        with pytest.raises(RuntimeError, match="retry"):
            generate_ai_quiz.run("11111111-1111-1111-1111-111111111111")

    def test_generate_ai_content_suggestion_writes_output(self):
        user = InstructorFactory()
        suggestion = AIContentSuggestion.objects.create(
            initiated_by=user,
            suggestion_type=AIContentSuggestion.SuggestionType.LESSON_OUTLINE,
            input_text="Teach testing",
        )

        generate_ai_content_suggestion.run(str(suggestion.id))

        suggestion.refresh_from_db()
        assert "placeholder" in suggestion.output_text.lower()

    @patch("apps.ai_tools.tasks.generate_ai_content_suggestion.retry", side_effect=RuntimeError("retry"))
    def test_generate_ai_content_suggestion_retries_on_error(self, _mocked_retry):
        with pytest.raises(RuntimeError, match="retry"):
            generate_ai_content_suggestion.run("11111111-1111-1111-1111-111111111111")
