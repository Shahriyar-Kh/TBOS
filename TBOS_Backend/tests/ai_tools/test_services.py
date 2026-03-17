import pytest

from apps.ai_tools.models import AIContentSuggestion, AIQuizGeneration
from apps.ai_tools.services.ai_service import AIService
from tests.factories import CourseFactory, InstructorFactory, QuizFactory


@pytest.mark.django_db
class TestAIToolsServices:
    def test_create_quiz_job_creates_pending_job(self):
        user = InstructorFactory()
        course = CourseFactory(instructor=user)

        job = AIService.create_quiz_job(user=user, course=course, prompt="Generate quiz", num_questions=6)

        assert job.status == AIQuizGeneration.Status.PENDING
        assert job.num_questions == 6

    def test_complete_quiz_job_marks_completed(self):
        user = InstructorFactory()
        course = CourseFactory(instructor=user)
        quiz = QuizFactory(course=course)
        job = AIService.create_quiz_job(user=user, course=course, prompt="Generate quiz")

        AIService.complete_quiz_job(job, quiz)
        job.refresh_from_db()

        assert job.status == AIQuizGeneration.Status.COMPLETED
        assert job.quiz == quiz

    def test_fail_quiz_job_sets_error_message(self):
        user = InstructorFactory()
        course = CourseFactory(instructor=user)
        job = AIService.create_quiz_job(user=user, course=course, prompt="Generate quiz")

        AIService.fail_quiz_job(job, "provider unavailable")
        job.refresh_from_db()

        assert job.status == AIQuizGeneration.Status.FAILED
        assert "provider unavailable" in job.error_message

    def test_create_suggestion_persists_content(self):
        user = InstructorFactory()
        suggestion = AIService.create_suggestion(
            user=user,
            suggestion_type=AIContentSuggestion.SuggestionType.COURSE_DESCRIPTION,
            input_text="Raw input",
            output_text="AI output",
        )
        assert suggestion.output_text == "AI output"
