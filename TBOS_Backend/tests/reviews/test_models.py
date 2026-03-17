import pytest
from django.db import IntegrityError

from tests.factories import CourseFactory, ReviewFactory, UserFactory


@pytest.mark.django_db
class TestReviewModels:
    def test_review_string_representation_contains_rating(self):
        review = ReviewFactory(rating=5)
        assert "5" in str(review)

    def test_unique_review_per_student_and_course(self):
        student = UserFactory()
        course = CourseFactory()
        ReviewFactory(student=student, course=course)
        with pytest.raises(IntegrityError):
            ReviewFactory(student=student, course=course)
