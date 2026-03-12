from django.conf import settings
from django.db import models

from apps.core.models import TimeStampedModel
from apps.courses.models import Course
from apps.lessons.models import Lesson


class Quiz(TimeStampedModel):
    """Defines quiz configuration for a lesson."""

    course = models.ForeignKey(
        Course, on_delete=models.CASCADE, related_name="quizzes"
    )
    lesson = models.OneToOneField(
        Lesson,
        on_delete=models.CASCADE,
        related_name="quiz",
        null=True,
        blank=True,
    )
    title = models.CharField(max_length=300)
    description = models.TextField(blank=True, default="")
    time_limit_minutes = models.PositiveIntegerField(
        null=True, blank=True, help_text="Time limit in minutes. Null = unlimited."
    )
    max_attempts = models.PositiveIntegerField(default=1)
    passing_score = models.PositiveIntegerField(
        default=50, help_text="Minimum percentage to pass."
    )
    shuffle_questions = models.BooleanField(default=False)
    shuffle_options = models.BooleanField(default=False)
    is_active = models.BooleanField(default=False)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = "quizzes"
        ordering = ["order"]
        indexes = [
            models.Index(fields=["course", "lesson"]),
        ]

    def __str__(self):
        return self.title


class Question(TimeStampedModel):
    """Stores quiz questions."""

    class QuestionType(models.TextChoices):
        MCQ = "mcq", "Multiple Choice"

    quiz = models.ForeignKey(
        Quiz, on_delete=models.CASCADE, related_name="questions"
    )
    question_text = models.TextField()
    question_type = models.CharField(
        max_length=20,
        choices=QuestionType.choices,
        default=QuestionType.MCQ,
    )
    order = models.PositiveIntegerField(default=0)
    points = models.PositiveIntegerField(default=1)
    explanation = models.TextField(blank=True, default="")

    class Meta:
        db_table = "questions"
        ordering = ["order"]

    def __str__(self):
        return self.question_text[:80]


class Option(TimeStampedModel):
    """Stores answer options for a question. Only one option should be correct."""

    question = models.ForeignKey(
        Question, on_delete=models.CASCADE, related_name="options"
    )
    option_text = models.CharField(max_length=500)
    is_correct = models.BooleanField(default=False)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = "options"
        ordering = ["order"]

    def __str__(self):
        return self.option_text


class QuizAttempt(TimeStampedModel):
    """Tracks quiz attempts by students."""

    class Status(models.TextChoices):
        IN_PROGRESS = "in_progress", "In Progress"
        SUBMITTED = "submitted", "Submitted"
        EXPIRED = "expired", "Expired"

    quiz = models.ForeignKey(
        Quiz, on_delete=models.CASCADE, related_name="attempts"
    )
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="quiz_attempts",
    )
    attempt_number = models.PositiveIntegerField(default=1)
    score = models.PositiveIntegerField(default=0)
    total_points = models.PositiveIntegerField(default=0)
    total_questions = models.PositiveIntegerField(default=0)
    correct_answers = models.PositiveIntegerField(default=0)
    percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    passed = models.BooleanField(default=False)
    start_time = models.DateTimeField(auto_now_add=True)
    end_time = models.DateTimeField(null=True, blank=True)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.IN_PROGRESS,
    )

    class Meta:
        db_table = "quiz_attempts"
        indexes = [
            models.Index(fields=["quiz", "student"]),
            models.Index(fields=["student", "status"]),
        ]

    def __str__(self):
        return f"{self.student.email} — {self.quiz.title} — {self.percentage}%"

    @property
    def is_completed(self):
        return self.status in (self.Status.SUBMITTED, self.Status.EXPIRED)


class StudentAnswer(TimeStampedModel):
    """Stores student responses for a quiz attempt."""

    attempt = models.ForeignKey(
        QuizAttempt, on_delete=models.CASCADE, related_name="answers"
    )
    question = models.ForeignKey(
        Question, on_delete=models.CASCADE, related_name="student_answers"
    )
    selected_option = models.ForeignKey(
        Option, on_delete=models.SET_NULL, null=True, blank=True
    )
    is_correct = models.BooleanField(default=False)

    class Meta:
        db_table = "student_answers"
        unique_together = [("attempt", "question")]

    def __str__(self):
        return f"Q: {self.question_id} — Correct: {self.is_correct}"
