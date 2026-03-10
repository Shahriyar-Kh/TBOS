from apps.ai_tools.models import AIContentSuggestion, AIQuizGeneration
from apps.courses.models import Course


class AIService:
    @staticmethod
    def create_quiz_job(user, course: Course, prompt: str, num_questions: int = 10):
        return AIQuizGeneration.objects.create(
            course=course,
            prompt=prompt,
            num_questions=num_questions,
            initiated_by=user,
            status=AIQuizGeneration.Status.PENDING,
        )

    @staticmethod
    def complete_quiz_job(job: AIQuizGeneration, quiz):
        job.quiz = quiz
        job.status = AIQuizGeneration.Status.COMPLETED
        job.save(update_fields=["quiz", "status", "updated_at"])
        return job

    @staticmethod
    def fail_quiz_job(job: AIQuizGeneration, error: str):
        job.status = AIQuizGeneration.Status.FAILED
        job.error_message = error
        job.save(update_fields=["status", "error_message", "updated_at"])
        return job

    @staticmethod
    def create_suggestion(user, suggestion_type: str, input_text: str, output_text: str, course=None):
        return AIContentSuggestion.objects.create(
            initiated_by=user,
            suggestion_type=suggestion_type,
            input_text=input_text,
            output_text=output_text,
            course=course,
        )
