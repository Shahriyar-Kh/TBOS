from django.conf import settings
from django.db import models

from apps.core.models import TimeStampedModel
from apps.courses.models import Course


class Enrollment(TimeStampedModel):
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="enrollments",
        db_index=True,
    )
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name="enrollments",
        db_index=True,
    )
    is_active = models.BooleanField(default=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    progress_percent = models.DecimalField(
        max_digits=5, decimal_places=2, default=0.00
    )
    last_accessed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "enrollments"
        unique_together = [("student", "course")]
        indexes = [
            models.Index(fields=["student", "is_active"]),
            models.Index(fields=["course", "is_active"]),
        ]

    def __str__(self):
        return f"{self.student.email} — {self.course.title}"


class LessonProgress(TimeStampedModel):
    """Track per-lesson completion."""
    enrollment = models.ForeignKey(
        Enrollment, on_delete=models.CASCADE, related_name="lesson_progress"
    )
    lesson = models.ForeignKey(
        "lessons.Lesson", on_delete=models.CASCADE, related_name="progress_records"
    )
    is_completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "lesson_progress"
        unique_together = [("enrollment", "lesson")]

    def __str__(self):
        return f"{self.enrollment.student.email} — {self.lesson.title}"
