from django.conf import settings
from django.db import models

from apps.core.models import TimeStampedModel
from apps.courses.models import Course
from apps.lessons.models import Lesson


class Assignment(TimeStampedModel):
    """Defines assignment configuration for a lesson."""

    class SubmissionType(models.TextChoices):
        FILE = "file", "File"
        TEXT = "text", "Text"
        FILE_AND_TEXT = "file_and_text", "File and Text"

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
    instructions = models.TextField(
        blank=True, default="",
        help_text="Detailed assignment instructions.",
    )
    instructions_url = models.URLField(
        max_length=500, blank=True, default="",
        help_text="URL to PDF/doc with instructions (Cloudinary/S3).",
    )
    max_score = models.PositiveIntegerField(default=100)
    submission_type = models.CharField(
        max_length=20,
        choices=SubmissionType.choices,
        default=SubmissionType.FILE_AND_TEXT,
    )
    due_date = models.DateTimeField(null=True, blank=True)
    allow_resubmission = models.BooleanField(default=True)
    max_attempts = models.PositiveIntegerField(default=1)
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


class AssignmentSubmission(TimeStampedModel):
    """Stores student assignment submissions."""

    class Status(models.TextChoices):
        SUBMITTED = "submitted", "Submitted"
        GRADED = "graded", "Graded"
        LATE = "late", "Late"
        REJECTED = "rejected", "Rejected"

    assignment = models.ForeignKey(
        Assignment, on_delete=models.CASCADE, related_name="submissions"
    )
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="assignment_submissions",
    )
    submission_text = models.TextField(blank=True, default="")
    file_url = models.URLField(
        max_length=500, blank=True, default="",
        help_text="Uploaded file URL (Cloudinary/S3).",
    )
    attempt_number = models.PositiveIntegerField(default=1)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.SUBMITTED,
        db_index=True,
    )
    submitted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "assignment_submissions"
        indexes = [
            models.Index(fields=["assignment", "student"]),
            models.Index(fields=["student", "status"]),
        ]
        unique_together = [("assignment", "student", "attempt_number")]

    def __str__(self):
        return f"{self.student.email} — {self.assignment.title} (#{self.attempt_number})"


class AssignmentGrade(TimeStampedModel):
    """Stores grading results for a submission."""

    submission = models.OneToOneField(
        AssignmentSubmission,
        on_delete=models.CASCADE,
        related_name="grade",
    )
    grader = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="graded_assignments",
    )
    score = models.PositiveIntegerField()
    feedback = models.TextField(blank=True, default="")
    graded_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "assignment_grades"
        indexes = [
            models.Index(fields=["submission"]),
        ]

    def __str__(self):
        return f"Grade: {self.score} — {self.submission}"


# Backward-compatible alias
Submission = AssignmentSubmission
