from django.conf import settings
from django.db import models

from apps.core.models import TimeStampedModel


class Notification(TimeStampedModel):
    class NotificationType(models.TextChoices):
        COURSE_UPDATE = "COURSE_UPDATE", "Course Update"
        NEW_LESSON = "NEW_LESSON", "New Lesson"
        QUIZ_AVAILABLE = "QUIZ_AVAILABLE", "Quiz Available"
        ASSIGNMENT_DEADLINE = "ASSIGNMENT_DEADLINE", "Assignment Deadline"
        CERTIFICATE_ISSUED = "CERTIFICATE_ISSUED", "Certificate Issued"
        SYSTEM_ALERT = "SYSTEM_ALERT", "System Alert"

    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications",
        db_index=True,
    )
    notification_type = models.CharField(
        max_length=32,
        choices=NotificationType.choices,
        default=NotificationType.SYSTEM_ALERT,
        db_index=True,
    )
    title = models.CharField(max_length=300)
    message = models.TextField()
    reference_id = models.UUIDField(null=True, blank=True)
    is_read = models.BooleanField(default=False, db_index=True)

    class Meta:
        db_table = "notifications"
        ordering = ["is_read", "-created_at"]
        indexes = [
            models.Index(fields=["recipient", "is_read"]),
            models.Index(fields=["recipient", "created_at"]),
        ]

    def __str__(self):
        return f"[{self.notification_type}] {self.title} → {self.recipient.email}"


class NotificationPreference(TimeStampedModel):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notification_preferences",
    )
    email_notifications_enabled = models.BooleanField(default=True)
    in_app_notifications_enabled = models.BooleanField(default=True)
    course_updates = models.BooleanField(default=True)
    assignment_notifications = models.BooleanField(default=True)
    quiz_notifications = models.BooleanField(default=True)

    class Meta:
        db_table = "notification_preferences"

    def __str__(self):
        return f"Notification preferences for {self.user.email}"
