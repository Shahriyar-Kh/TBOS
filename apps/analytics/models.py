from django.conf import settings
from django.db import models

from apps.core.models import TimeStampedModel
from apps.courses.models import Course
from apps.videos.models import Video


class CourseAnalytics(TimeStampedModel):
    """Aggregated analytics per course — updated periodically by Celery."""
    course = models.OneToOneField(
        Course, on_delete=models.CASCADE, related_name="analytics"
    )
    total_views = models.PositiveIntegerField(default=0)
    total_watch_time_seconds = models.PositiveBigIntegerField(default=0)
    total_completions = models.PositiveIntegerField(default=0)
    avg_completion_percent = models.DecimalField(
        max_digits=5, decimal_places=2, default=0
    )
    total_revenue = models.DecimalField(
        max_digits=12, decimal_places=2, default=0
    )
    snapshot_date = models.DateField(auto_now=True)

    class Meta:
        db_table = "course_analytics"

    def __str__(self):
        return f"Analytics: {self.course.title}"


class UserActivity(TimeStampedModel):
    """Track individual user activity events."""

    class EventType(models.TextChoices):
        VIDEO_WATCHED = "video_watched", "Video Watched"
        LESSON_COMPLETED = "lesson_completed", "Lesson Completed"
        QUIZ_COMPLETED = "quiz_completed", "Quiz Completed"
        ASSIGNMENT_SUBMITTED = "assignment_submitted", "Assignment Submitted"
        COURSE_COMPLETED = "course_completed", "Course Completed"
        LOGIN = "login", "Login"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="activities",
        db_index=True,
    )
    event_type = models.CharField(
        max_length=30, choices=EventType.choices, db_index=True
    )
    course = models.ForeignKey(
        Course,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="activities",
    )
    video = models.ForeignKey(
        Video,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = "user_activities"
        indexes = [
            models.Index(fields=["user", "event_type", "created_at"]),
            models.Index(fields=["course", "event_type"]),
        ]

    def __str__(self):
        return f"{self.user.email} — {self.event_type}"
