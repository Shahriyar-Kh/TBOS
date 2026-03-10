from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from apps.core.models import TimeStampedModel
from apps.courses.models import Course


class Review(TimeStampedModel):
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="reviews",
    )
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name="reviews",
    )
    rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    content = models.TextField(max_length=2000)

    class Meta:
        db_table = "reviews"
        unique_together = [("student", "course")]
        indexes = [
            models.Index(fields=["course", "rating"]),
        ]

    def __str__(self):
        return f"{self.student.email} — {self.course.title} — {self.rating}★"
