from django.conf import settings
from django.db import models

from apps.core.models import TimeStampedModel


class Notification(TimeStampedModel):
    class NotificationType(models.TextChoices):
        ENROLLMENT = "enrollment", "Enrollment"
        PAYMENT = "payment", "Payment"
        ASSIGNMENT = "assignment", "Assignment"
        QUIZ = "quiz", "Quiz"
        GRADE = "grade", "Grade"
        CERTIFICATE = "certificate", "Certificate"
        ANNOUNCEMENT = "announcement", "Announcement"
        SYSTEM = "system", "System"

    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications",
        db_index=True,
    )
    notification_type = models.CharField(
        max_length=20,
        choices=NotificationType.choices,
        default=NotificationType.SYSTEM,
        db_index=True,
    )
    title = models.CharField(max_length=300)
    message = models.TextField()
    is_read = models.BooleanField(default=False, db_index=True)
    action_url = models.CharField(max_length=500, blank=True, default="")

    class Meta:
        db_table = "notifications"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["recipient", "is_read"]),
            models.Index(fields=["recipient", "notification_type"]),
        ]

    def __str__(self):
        return f"[{self.notification_type}] {self.title} → {self.recipient.email}"
