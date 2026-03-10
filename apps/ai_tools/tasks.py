from celery import shared_task


@shared_task(bind=True, max_retries=2)
def generate_ai_quiz(self, job_id):
    """
    Generate quiz questions using AI.
    This is a placeholder — integrate your preferred AI provider
    (OpenAI, Gemini, etc.) here.
    """
    from apps.ai_tools.models import AIQuizGeneration
    from apps.quiz.models import Quiz, Question, Option

    try:
        job = AIQuizGeneration.objects.select_related("course").get(id=job_id)
        job.status = AIQuizGeneration.Status.PROCESSING
        job.save(update_fields=["status"])

        # TODO: Replace with actual AI API call
        # Example structure expected from AI:
        # questions = [
        #     {
        #         "text": "What is ...?",
        #         "options": [
        #             {"text": "Option A", "is_correct": False},
        #             {"text": "Option B", "is_correct": True},
        #             ...
        #         ]
        #     },
        #     ...
        # ]

        # Placeholder: mark as completed with note
        job.status = AIQuizGeneration.Status.COMPLETED
        job.error_message = "AI provider not configured. Implement generate_ai_quiz task."
        job.save(update_fields=["status", "error_message"])

    except Exception as exc:
        AIQuizGeneration.objects.filter(id=job_id).update(
            status=AIQuizGeneration.Status.FAILED,
            error_message=str(exc)[:500],
        )
        raise self.retry(exc=exc, countdown=120)


@shared_task(bind=True, max_retries=2)
def generate_ai_content_suggestion(self, suggestion_id):
    """
    Generate content suggestion using AI.
    Placeholder — integrate your preferred AI provider.
    """
    from apps.ai_tools.models import AIContentSuggestion

    try:
        suggestion = AIContentSuggestion.objects.get(id=suggestion_id)

        # TODO: Replace with actual AI API call
        suggestion.output_text = (
            f"[AI Placeholder] Suggestion for: {suggestion.input_text[:100]}"
        )
        suggestion.save(update_fields=["output_text"])

    except Exception as exc:
        raise self.retry(exc=exc, countdown=60)
