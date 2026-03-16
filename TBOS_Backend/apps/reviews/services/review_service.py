from django.db import models, transaction

from apps.courses.models import Course
from apps.reviews.models import Review, ReviewResponse


class ReviewService:

    @staticmethod
    @transaction.atomic
    def create_review(student, course, rating, review_text):
        review = Review.objects.create(
            student=student,
            course=course,
            rating=rating,
            review_text=review_text,
        )
        ReviewService._refresh_course_rating(course)
        return review

    @staticmethod
    @transaction.atomic
    def update_review(review, rating=None, review_text=None):
        if rating is not None:
            review.rating = rating
        if review_text is not None:
            review.review_text = review_text
        review.save(update_fields=["rating", "review_text", "updated_at"])
        ReviewService._refresh_course_rating(review.course)
        return review

    @staticmethod
    @transaction.atomic
    def delete_review(review):
        course = review.course
        review.delete()
        ReviewService._refresh_course_rating(course)

    @staticmethod
    @transaction.atomic
    def add_instructor_response(review, instructor, response_text):
        response, created = ReviewResponse.objects.update_or_create(
            review=review,
            defaults={
                "instructor": instructor,
                "response_text": response_text,
            },
        )
        return response

    @staticmethod
    def calculate_course_rating(course):
        agg = Review.objects.filter(
            course=course, status=Review.Status.PUBLISHED
        ).aggregate(
            avg=models.Avg("rating"),
            count=models.Count("id"),
        )
        return {
            "average_rating": round(agg["avg"] or 0, 2),
            "rating_count": agg["count"] or 0,
        }

    @staticmethod
    def get_course_reviews(course):
        return (
            Review.objects.filter(course=course, status=Review.Status.PUBLISHED)
            .select_related("student")
            .prefetch_related("instructor_response__instructor")
            .order_by("-created_at")
        )

    @staticmethod
    def _refresh_course_rating(course):
        stats = ReviewService.calculate_course_rating(course)
        course.average_rating = stats["average_rating"]
        course.rating_count = stats["rating_count"]
        course.save(update_fields=["average_rating", "rating_count"])
