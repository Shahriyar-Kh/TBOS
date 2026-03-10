from django.conf import settings
from django.db import models

from apps.core.models import TimeStampedModel
from apps.courses.models import Course
from apps.lessons.models import Lesson


class Assignment(TimeStampedModel):
    course = models.ForeignKey(
        Course, on_delete=models.CASCADE, related_name="assignments"
    )
    lesson = models.ForeignKey(
        Lesson,
        on_delete=models.CASCADE,
        related_name="assignments",
        null=True,
        blank=True,
    )
    title = models.CharField(max_length=300)
    description = models.TextField()
    instructions_url = models.URLField(
        max_length=500, blank=True, default="",
        help_text="URL to PDF/doc with instructions (Cloudinary/S3).",
    )
    max_score = models.PositiveIntegerField(default=100)
    due_date = models.DateTimeField(null=True, blank=True)
    time_limit_minutes = models.PositiveIntegerField(
        null=True, blank=True, help_text="Time limit in minutes."
    )
    is_published = models.BooleanField(default=False)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = "assignments"
        ordering = ["order"]
        indexes = [
            models.Index(fields=["course", "lesson"]),
        ]

    def __str__(self):
        return f"{self.title} — {self.course.title}"


class Submission(TimeStampedModel):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        SUBMITTED = "submitted", "Submitted"
        GRADED = "graded", "Graded"
        LATE = "late", "Late"
        RETURNED = "returned", "Returned"

    assignment = models.ForeignKey(
        Assignment, on_delete=models.CASCADE, related_name="submissions"
    )
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="submissions",
    )
    submission_text = models.TextField(blank=True, default="")
    file_url = models.URLField(
        max_length=500, blank=True, default="",
        help_text="Uploaded file URL (Cloudinary/S3).",
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True,
    )
    score = models.PositiveIntegerField(null=True, blank=True)
    feedback = models.TextField(blank=True, default="")
    graded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="graded_submissions",
    )
    graded_at = models.DateTimeField(null=True, blank=True)
    submitted_at = models.DateTimeField(null=True, blank=True)
    started_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "submissions"
        indexes = [
            models.Index(fields=["assignment", "student"]),
            models.Index(fields=["student", "status"]),
        ]
        unique_together = [("assignment", "student")]

    def __str__(self):
        return f"{self.student.email} — {self.assignment.title}"
