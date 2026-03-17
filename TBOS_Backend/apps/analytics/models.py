from django.conf import settings
from django.db import models
from django.utils import timezone

from apps.core.models import TimeStampedModel
from apps.courses.models import Course


class CourseAnalytics(TimeStampedModel):
    """Aggregated analytics snapshot for course performance dashboards."""

    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name="analytics_snapshots",
        db_index=True,
    )
    total_students = models.PositiveIntegerField(default=0)
    total_lessons = models.PositiveIntegerField(default=0)
    completed_students = models.PositiveIntegerField(default=0)
    average_progress = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    average_quiz_score = models.DecimalField(
        max_digits=5, decimal_places=2, default=0
    )
    average_assignment_score = models.DecimalField(
        max_digits=5, decimal_places=2, default=0
    )
    total_revenue = models.DecimalField(
        max_digits=12, decimal_places=2, default=0
    )
    rating_average = models.DecimalField(max_digits=3, decimal_places=2, default=0)
    last_updated = models.DateTimeField(auto_now=True, db_index=True)

    class Meta:
        db_table = "course_analytics"
        indexes = [
            models.Index(fields=["course", "last_updated"], name="course_analy_course_last_idx"),
        ]

    def __str__(self):
        return f"Analytics: {self.course.title}"


class UserActivity(TimeStampedModel):
    """Track individual user activity events."""

    class ActivityType(models.TextChoices):
        VIDEO_WATCH = "VIDEO_WATCH", "Video Watch"
        QUIZ_ATTEMPT = "QUIZ_ATTEMPT", "Quiz Attempt"
        ASSIGNMENT_SUBMIT = "ASSIGNMENT_SUBMIT", "Assignment Submit"
        COURSE_COMPLETE = "COURSE_COMPLETE", "Course Complete"
        LOGIN = "LOGIN", "Login"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="activities",
        db_index=True,
    )
    activity_type = models.CharField(
        max_length=30, choices=ActivityType.choices, db_index=True
    )
    reference_id = models.UUIDField(null=True, blank=True, db_index=True)
    timestamp = models.DateTimeField(default=timezone.now, db_index=True)

    class Meta:
        db_table = "user_activities"
        indexes = [
            models.Index(fields=["user", "timestamp"], name="user_activi_user_time_idx"),
            models.Index(fields=["activity_type", "timestamp"], name="user_activi_type_time_idx"),
        ]

    def __str__(self):
        return f"{self.user.email} — {self.activity_type}"
