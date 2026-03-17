import pytest
from rest_framework.test import APIRequestFactory

from apps.reviews.serializers import ReviewCreateSerializer
from tests.factories import CourseFactory, EnrollmentFactory, UserFactory


@pytest.mark.django_db
class TestReviewSerializers:
    def test_review_create_serializer_requires_active_enrollment(self):
        student = UserFactory()
        course = CourseFactory()
        request = APIRequestFactory().post("/api/v1/reviews/student/")
        request.user = student
        serializer = ReviewCreateSerializer(
            data={"course_id": str(course.id), "rating": 5, "review_text": "Great"},
            context={"request": request},
        )
        assert not serializer.is_valid()

    def test_review_create_serializer_valid_for_enrolled_student(self):
        student = UserFactory()
        course = CourseFactory(status="published")
        EnrollmentFactory(student=student, course=course, is_active=True)
        request = APIRequestFactory().post("/api/v1/reviews/student/")
        request.user = student
        serializer = ReviewCreateSerializer(
            data={"course_id": str(course.id), "rating": 4, "review_text": "Solid"},
            context={"request": request},
        )
        assert serializer.is_valid(), serializer.errors
