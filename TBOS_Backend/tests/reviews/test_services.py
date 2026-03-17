from decimal import Decimal

import pytest

from apps.reviews.services.review_service import ReviewService
from tests.factories import CourseFactory, ReviewFactory, UserFactory


@pytest.mark.django_db
class TestReviewService:
    def test_create_review_updates_course_aggregate_rating(self):
        student = UserFactory()
        course = CourseFactory(status="published")

        ReviewService.create_review(
            student=student,
            course=course,
            rating=5,
            review_text="Excellent course",
        )

        course.refresh_from_db()
        assert course.rating_count == 1
        assert Decimal(str(course.average_rating)) == Decimal("5")

    def test_delete_review_recalculates_rating(self):
        course = CourseFactory(status="published")
        review = ReviewFactory(course=course, rating=2)

        ReviewService.delete_review(review)

        course.refresh_from_db()
        assert course.rating_count == 0
        assert Decimal(str(course.average_rating)) == Decimal("0")
