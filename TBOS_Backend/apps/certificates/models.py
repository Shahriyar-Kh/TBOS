import uuid

from django.conf import settings
from django.db import models

from apps.core.models import TimeStampedModel
from apps.courses.models import Course


def generate_certificate_number():
    return f"TBOS-{uuid.uuid4().hex[:8].upper()}"


class Certificate(TimeStampedModel):
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="certificates",
    )
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name="certificates",
    )
    certificate_number = models.CharField(
        max_length=50,
        unique=True,
        default=generate_certificate_number,
        db_index=True,
    )
    issued_at = models.DateTimeField(auto_now_add=True)
    pdf_url = models.URLField(max_length=500, blank=True, default="")

    class Meta:
        db_table = "certificates"
        unique_together = [("student", "course")]
        indexes = [
            models.Index(fields=["student", "course"]),
        ]

    def __str__(self):
        return f"{self.certificate_number} — {self.student.email}"
