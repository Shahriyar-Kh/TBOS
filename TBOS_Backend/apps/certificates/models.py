import uuid

from django.conf import settings
from django.db import models
from django.utils import timezone

from apps.core.models import TimeStampedModel
from apps.courses.models import Course


def generate_certificate_number():
    """Kept for backward compatibility with historical migrations."""
    return f"TBOS-{uuid.uuid4().hex[:8].upper()}"


class Certificate(TimeStampedModel):
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="certificates",
        db_index=True,
    )
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name="certificates",
        db_index=True,
    )
    certificate_number = models.CharField(
        max_length=50,
        unique=True,
        db_index=True,
    )
    issue_date = models.DateField(default=timezone.now)
    verification_code = models.CharField(max_length=128, unique=True, db_index=True)
    certificate_url = models.URLField(max_length=500, blank=True, default="")

    class Meta:
        db_table = "certificates"
        constraints = [
            models.UniqueConstraint(
                fields=["student", "course"],
                name="unique_certificate_per_student_course",
            ),
        ]
        indexes = [
            models.Index(fields=["student"], name="cert_student_idx"),
            models.Index(fields=["course"], name="cert_course_idx"),
            models.Index(fields=["verification_code"], name="cert_verify_code_idx"),
        ]

    def __str__(self):
        return f"{self.certificate_number} — {self.student.email}"
