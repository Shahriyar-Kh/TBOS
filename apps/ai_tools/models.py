from django.conf import settings
from django.db import models

from apps.core.models import TimeStampedModel
from apps.courses.models import Course
from apps.quiz.models import Quiz


class AIQuizGeneration(TimeStampedModel):
    """Track AI-generated quiz jobs."""

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        PROCESSING = "processing", "Processing"
        COMPLETED = "completed", "Completed"
        FAILED = "failed", "Failed"

    course = models.ForeignKey(
        Course, on_delete=models.CASCADE, related_name="ai_quiz_jobs"
    )
    quiz = models.ForeignKey(
        Quiz,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="ai_generation",
    )
    prompt = models.TextField(help_text="Topic/content to generate quiz from.")
    num_questions = models.PositiveIntegerField(default=10)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )
    error_message = models.TextField(blank=True, default="")
    initiated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="ai_quiz_jobs",
    )

    class Meta:
        db_table = "ai_quiz_generations"

    def __str__(self):
        return f"AI Quiz: {self.course.title} — {self.status}"


class AIContentSuggestion(TimeStampedModel):
    """Store AI-generated content suggestions."""

    class SuggestionType(models.TextChoices):
        COURSE_DESCRIPTION = "course_description", "Course Description"
        LESSON_OUTLINE = "lesson_outline", "Lesson Outline"
        LEARNING_OUTCOMES = "learning_outcomes", "Learning Outcomes"
        ASSIGNMENT_PROMPT = "assignment_prompt", "Assignment Prompt"

    initiated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="ai_suggestions",
    )
    suggestion_type = models.CharField(
        max_length=30, choices=SuggestionType.choices
    )
    input_text = models.TextField()
    output_text = models.TextField(blank=True, default="")
    course = models.ForeignKey(
        Course,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="ai_suggestions",
    )

    class Meta:
        db_table = "ai_content_suggestions"

    def __str__(self):
        return f"{self.suggestion_type} by {self.initiated_by.email}"
