from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from apps.core.models import TimeStampedModel
from apps.courses.models import Course


class Review(TimeStampedModel):

    class Status(models.TextChoices):
        PUBLISHED = "published", "Published"
        PENDING = "pending", "Pending"
        REJECTED = "rejected", "Rejected"

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
    review_text = models.TextField(max_length=2000)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PUBLISHED,
        db_index=True,
    )

    class Meta:
        db_table = "reviews"
        unique_together = [("student", "course")]
        indexes = [
            models.Index(fields=["course", "rating"]),
            models.Index(fields=["student"]),
        ]

    def __str__(self):
        return f"{self.student.email} — {self.course.title} — {self.rating}★"


class ReviewResponse(TimeStampedModel):
    review = models.OneToOneField(
        Review,
        on_delete=models.CASCADE,
        related_name="instructor_response",
    )
    instructor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="review_responses",
    )
    response_text = models.TextField(max_length=2000)

    class Meta:
        db_table = "review_responses"

    def __str__(self):
        return f"Response by {self.instructor.email} on {self.review}"
