from django.conf import settings
from django.db import models
from django.utils import timezone

from apps.core.models import TimeStampedModel
from apps.courses.models import Course


class Enrollment(TimeStampedModel):

    class EnrollmentStatus(models.TextChoices):
        ACTIVE = "active", "Active"
        COMPLETED = "completed", "Completed"
        CANCELLED = "cancelled", "Cancelled"

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
    enrollment_status = models.CharField(
        max_length=20,
        choices=EnrollmentStatus.choices,
        default=EnrollmentStatus.ACTIVE,
        db_index=True,
    )
    is_active = models.BooleanField(default=True)
    progress_percentage = models.DecimalField(
        max_digits=5, decimal_places=2, default=0.00
    )
    completed_lessons_count = models.PositiveIntegerField(default=0)
    total_lessons_count = models.PositiveIntegerField(default=0)
    enrolled_at = models.DateTimeField(default=timezone.now)
    completed_at = models.DateTimeField(null=True, blank=True)
    last_accessed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "enrollments"
        unique_together = [("student", "course")]
        indexes = [
            models.Index(fields=["student", "is_active"]),
            models.Index(fields=["course", "is_active"]),
            models.Index(fields=["enrollment_status"]),
        ]

    def __str__(self):
        return f"{self.student.email} — {self.course.title}"


class LessonProgress(TimeStampedModel):
    """Track per-lesson completion."""

    enrollment = models.ForeignKey(
        Enrollment, on_delete=models.CASCADE, related_name="lesson_progress"
    )
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="lesson_progress",
        null=True,
        blank=True,
        db_index=True,
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


class VideoProgress(TimeStampedModel):
    """Track video watch progress so students can resume."""

    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="video_progress",
        db_index=True,
    )
    video = models.ForeignKey(
        "videos.Video", on_delete=models.CASCADE, related_name="progress_records"
    )
    watch_time_seconds = models.PositiveIntegerField(default=0)
    last_position_seconds = models.PositiveIntegerField(default=0)
    is_completed = models.BooleanField(default=False)

    class Meta:
        db_table = "video_progress"
        unique_together = [("student", "video")]

    def __str__(self):
        return f"{self.student.email} — {self.video.title}"
