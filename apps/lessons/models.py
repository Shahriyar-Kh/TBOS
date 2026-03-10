from django.db import models

from apps.core.models import TimeStampedModel
from apps.courses.models import Course


class Lesson(TimeStampedModel):
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name="lessons",
        db_index=True,
    )
    title = models.CharField(max_length=300)
    description = models.TextField(blank=True, default="")
    order = models.PositiveIntegerField(default=0, db_index=True)
    is_published = models.BooleanField(default=False)
    duration_minutes = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = "lessons"
        ordering = ["order"]
        unique_together = [("course", "order")]
        indexes = [
            models.Index(fields=["course", "order"]),
        ]

    def __str__(self):
        return f"{self.order}. {self.title} — {self.course.title}"
