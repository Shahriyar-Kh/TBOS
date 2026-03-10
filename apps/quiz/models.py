from django.conf import settings
from django.db import models

from apps.core.models import TimeStampedModel
from apps.courses.models import Course
from apps.lessons.models import Lesson


class Quiz(TimeStampedModel):
    course = models.ForeignKey(
        Course, on_delete=models.CASCADE, related_name="quizzes"
    )
    lesson = models.ForeignKey(
        Lesson,
        on_delete=models.CASCADE,
        related_name="quizzes",
        null=True,
        blank=True,
    )
    title = models.CharField(max_length=300)
    description = models.TextField(blank=True, default="")
    time_limit_minutes = models.PositiveIntegerField(
        null=True, blank=True, help_text="Time limit in minutes. Null = unlimited."
    )
    max_attempts = models.PositiveIntegerField(default=1)
    pass_percentage = models.PositiveIntegerField(default=50)
    is_published = models.BooleanField(default=False)
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
    quiz = models.ForeignKey(
        Quiz, on_delete=models.CASCADE, related_name="questions"
    )
    text = models.TextField()
    order = models.PositiveIntegerField(default=0)
    points = models.PositiveIntegerField(default=1)

    class Meta:
        db_table = "questions"
        ordering = ["order"]

    def __str__(self):
        return self.text[:80]


class Option(TimeStampedModel):
    question = models.ForeignKey(
        Question, on_delete=models.CASCADE, related_name="options"
    )
    text = models.CharField(max_length=500)
    is_correct = models.BooleanField(default=False)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = "options"
        ordering = ["order"]

    def __str__(self):
        return self.text


class QuizAttempt(TimeStampedModel):
    quiz = models.ForeignKey(
        Quiz, on_delete=models.CASCADE, related_name="attempts"
    )
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="quiz_attempts",
    )
    score = models.PositiveIntegerField(default=0)
    total_points = models.PositiveIntegerField(default=0)
    percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    passed = models.BooleanField(default=False)
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    is_completed = models.BooleanField(default=False)
    current_question_index = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = "quiz_attempts"
        indexes = [
            models.Index(fields=["quiz", "student"]),
            models.Index(fields=["student", "is_completed"]),
        ]

    def __str__(self):
        return f"{self.student.email} — {self.quiz.title} — {self.percentage}%"


class QuizAnswer(TimeStampedModel):
    attempt = models.ForeignKey(
        QuizAttempt, on_delete=models.CASCADE, related_name="answers"
    )
    question = models.ForeignKey(
        Question, on_delete=models.CASCADE, related_name="quiz_answers"
    )
    selected_option = models.ForeignKey(
        Option, on_delete=models.SET_NULL, null=True, blank=True
    )
    is_correct = models.BooleanField(default=False)

    class Meta:
        db_table = "quiz_answers"
        unique_together = [("attempt", "question")]

    def __str__(self):
        return f"Q: {self.question_id} — Correct: {self.is_correct}"
