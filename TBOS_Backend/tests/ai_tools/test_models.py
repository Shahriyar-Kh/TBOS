import pytest

from apps.ai_tools.models import AIContentSuggestion, AIQuizGeneration
from tests.factories import CourseFactory, InstructorFactory


@pytest.mark.django_db
class TestAIToolsModels:
    def test_ai_quiz_generation_str_contains_status(self):
        user = InstructorFactory()
        course = CourseFactory(instructor=user)
        job = AIQuizGeneration.objects.create(
            course=course,
            prompt="Generate quiz",
            num_questions=5,
            initiated_by=user,
        )
        assert "pending" in str(job).lower()

    def test_ai_content_suggestion_str_contains_user(self):
        user = InstructorFactory()
        suggestion = AIContentSuggestion.objects.create(
            initiated_by=user,
            suggestion_type=AIContentSuggestion.SuggestionType.LESSON_OUTLINE,
            input_text="Teach Django",
        )
        assert user.email in str(suggestion)
