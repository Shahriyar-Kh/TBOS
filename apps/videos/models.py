from django.db import models

from apps.core.models import TimeStampedModel
from apps.courses.models import Course
from apps.lessons.models import Lesson


class Video(TimeStampedModel):
    class SourceType(models.TextChoices):
        YOUTUBE = "youtube", "YouTube"
        CLOUDINARY = "cloudinary", "Cloudinary"
        AWS_S3 = "aws_s3", "AWS S3"

    lesson = models.ForeignKey(
        Lesson,
        on_delete=models.CASCADE,
        related_name="videos",
        db_index=True,
    )
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name="videos",
        db_index=True,
    )
    title = models.CharField(max_length=300)
    description = models.TextField(blank=True, default="")
    order = models.PositiveIntegerField(default=0)
    source_type = models.CharField(
        max_length=20,
        choices=SourceType.choices,
        default=SourceType.YOUTUBE,
        db_index=True,
    )
    # YouTube fields
    youtube_id = models.CharField(max_length=50, blank=True, default="")
    # Cloudinary fields
    cloudinary_public_id = models.CharField(max_length=300, blank=True, default="")
    cloudinary_url = models.URLField(max_length=500, blank=True, default="")
    # AWS S3 fields
    s3_key = models.CharField(max_length=500, blank=True, default="")
    s3_bucket = models.CharField(max_length=200, blank=True, default="")
    s3_url = models.URLField(max_length=500, blank=True, default="")

    thumbnail = models.URLField(max_length=500, blank=True, default="")
    duration_seconds = models.PositiveIntegerField(default=0)
    is_preview = models.BooleanField(default=False)
    is_published = models.BooleanField(default=True)

    class Meta:
        db_table = "videos"
        ordering = ["order"]
        indexes = [
            models.Index(fields=["lesson", "order"]),
            models.Index(fields=["course", "source_type"]),
        ]

    def __str__(self):
        return self.title

    @property
    def playback_url(self):
        if self.source_type == self.SourceType.YOUTUBE:
            return f"https://www.youtube.com/watch?v={self.youtube_id}"
        if self.source_type == self.SourceType.CLOUDINARY:
            return self.cloudinary_url
        if self.source_type == self.SourceType.AWS_S3:
            return self.s3_url
        return ""


class YouTubePlaylistImport(TimeStampedModel):
    """Track YouTube playlist import jobs."""

    class ImportStatus(models.TextChoices):
        PENDING = "pending", "Pending"
        PROCESSING = "processing", "Processing"
        COMPLETED = "completed", "Completed"
        FAILED = "failed", "Failed"

    course = models.ForeignKey(
        Course, on_delete=models.CASCADE, related_name="playlist_imports"
    )
    lesson = models.ForeignKey(
        Lesson, on_delete=models.CASCADE, related_name="playlist_imports"
    )
    playlist_url = models.URLField(max_length=500)
    status = models.CharField(
        max_length=20,
        choices=ImportStatus.choices,
        default=ImportStatus.PENDING,
    )
    videos_imported = models.PositiveIntegerField(default=0)
    error_message = models.TextField(blank=True, default="")
    initiated_by = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True,
        related_name="playlist_imports",
    )

    class Meta:
        db_table = "youtube_playlist_imports"

    def __str__(self):
        return f"Playlist import for {self.course.title} — {self.status}"
