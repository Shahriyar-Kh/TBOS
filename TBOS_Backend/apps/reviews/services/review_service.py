from django.db import models, transaction

from apps.courses.models import Course
from apps.reviews.models import Review


class ReviewService:
    @staticmethod
    @transaction.atomic
    def create_or_update_review(student, course: Course, rating: int, content: str) -> Review:
        review, created = Review.objects.update_or_create(
            student=student,
            course=course,
            defaults={"rating": rating, "content": content},
        )
        ReviewService._refresh_course_rating(course)
        return review

    @staticmethod
    def _refresh_course_rating(course: Course):
        agg = course.reviews.aggregate(
            avg=models.Avg("rating"), count=models.Count("id")
        )
        course.average_rating = round(agg["avg"] or 0, 2)
        course.total_reviews = agg["count"]
        course.save(update_fields=["average_rating", "total_reviews"])
