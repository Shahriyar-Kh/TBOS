"""Tests for review API views."""
import pytest
from decimal import Decimal
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken

from apps.courses.models import Course
from apps.reviews.models import Review, ReviewResponse
from tests.factories import (
    AdminFactory,
    CourseFactory,
    EnrollmentFactory,
    InstructorFactory,
    ReviewFactory,
    ReviewResponseFactory,
    UserFactoy,
)

BASE = "/api/v1/reviews"


# ──────────────────────────────────────────────
# Fixtures
# ──────────────────────────────────────────────


@pytest.fixture
def student(db):
    return UserFactory()


@pytest.fixture
def student2(db):
    return UserFactory()


@pytest.fixture
def instructor(db):
    return InstructorFactory()


@pytest.fixture
def admin(db):
    return AdminFactory()


def auth(api_client, user):
    token = str(RefreshToken.for_user(user).access_token)
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    return api_client


@pytest.fixture
def course(instructor):
    return CourseFactory(instructor=instructor, status=Course.Status.PUBLISHED)


@pytest.fixture
def enrolled_student(student, course):
    EnrollmentFactory(student=student, course=course)
    return student


@pytest.fixture
def enrolled_student2(student2, course):
    EnrollmentFactory(student=student2, course=course)
    return student2


@pytest.fixture
def review(enrolled_student, course):
    return ReviewFactory(student=enrolled_student, course=course, rating=4)


# ──────────────────────────────────────────────
# Student: Review CRUD
# ──────────────────────────────────────────────


@pytest.mark.django_db
class TestStudentReviewCRUD:
    url = f"{BASE}/student/"

    def test_create_review(self, api_client, enrolled_student, course):
        client = auth(api_client, enrolled_student)
        data = {
            "course_id": str(course.id),
            "rating": 5,
            "review_text": "Excellent course! Learned a lot.",
        }
        resp = client.post(self.url, data, format="json")
        assert resp.status_code == status.HTTP_201_CREATED
        assert resp.data["data"]["rating"] == 5
        assert resp.data["data"]["review_text"] == "Excellent course! Learned a lot."

    def test_create_review_updates_course_rating(self, api_client, enrolled_student, course):
        client = auth(api_client, enrolled_student)
        data = {
            "course_id": str(course.id),
            "rating": 4,
            "review_text": "Good course.",
        }
        resp = client.post(self.url, data, format="json")
        assert resp.status_code == status.HTTP_201_CREATED
        course.refresh_from_db()
        assert course.average_rating == Decimal("4.00")
        assert course.rating_count == 1

    def test_cannot_review_without_enrollment(self, api_client, student, course):
        client = auth(api_client, student)
        data = {
            "course_id": str(course.id),
            "rating": 5,
            "review_text": "Great!",
        }
        resp = client.post(self.url, data, format="json")
        assert resp.status_code == status.HTTP_400_BAD_REQUEST

    def test_cannot_review_same_course_twice(self, api_client, enrolled_student, course, review):
        client = auth(api_client, enrolled_student)
        data = {
            "course_id": str(course.id),
            "rating": 3,
            "review_text": "Another review.",
        }
        resp = client.post(self.url, data, format="json")
        assert resp.status_code == status.HTTP_400_BAD_REQUEST

    def test_instructor_cannot_review_own_course(self, api_client, instructor, course):
        # Enroll instructor first (edge case)
        EnrollmentFactory(student=instructor, course=course)
        client = auth(api_client, instructor)
        data = {
            "course_id": str(course.id),
            "rating": 5,
            "review_text": "My own course is great!",
        }
        resp = client.post(self.url, data, format="json")
        # Instructor role blocks StudentReview access
        assert resp.status_code == status.HTTP_403_FORBIDDEN

    def test_rating_must_be_between_1_and_5(self, api_client, enrolled_student, course):
        client = auth(api_client, enrolled_student)
        data = {
            "course_id": str(course.id),
            "rating": 0,
            "review_text": "Bad rating.",
        }
        resp = client.post(self.url, data, format="json")
        assert resp.status_code == status.HTTP_400_BAD_REQUEST

    def test_update_review(self, api_client, enrolled_student, review):
        client = auth(api_client, enrolled_student)
        url = f"{self.url}{review.id}/"
        data = {"rating": 3, "review_text": "Updated my review."}
        resp = client.put(url, data, format="json")
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data["data"]["rating"] == 3

    def test_partial_update_review(self, api_client, enrolled_student, review):
        client = auth(api_client, enrolled_student)
        url = f"{self.url}{review.id}/"
        resp = client.patch(url, {"rating": 2}, format="json")
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data["data"]["rating"] == 2

    def test_update_review_refreshes_course_rating(self, api_client, enrolled_student, course, review):
        client = auth(api_client, enrolled_student)
        url = f"{self.url}{review.id}/"
        resp = client.put(url, {"rating": 2, "review_text": "Meh."}, format="json")
        assert resp.status_code == status.HTTP_200_OK
        course.refresh_from_db()
        assert course.average_rating == Decimal("2.00")

    def test_delete_review(self, api_client, enrolled_student, course, review):
        client = auth(api_client, enrolled_student)
        url = f"{self.url}{review.id}/"
        resp = client.delete(url)
        assert resp.status_code == status.HTTP_200_OK
        assert Review.objects.filter(id=review.id).count() == 0
        course.refresh_from_db()
        assert course.average_rating == Decimal("0.00")
        assert course.rating_count == 0

    def test_list_own_reviews(self, api_client, enrolled_student, review):
        client = auth(api_client, enrolled_student)
        resp = client.get(self.url)
        assert resp.status_code == status.HTTP_200_OK

    def test_retrieve_review(self, api_client, enrolled_student, review):
        client = auth(api_client, enrolled_student)
        url = f"{self.url}{review.id}/"
        resp = client.get(url)
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data["data"]["id"] == str(review.id)

    def test_cannot_edit_other_student_review(self, api_client, enrolled_student2, review):
        client = auth(api_client, enrolled_student2)
        url = f"{self.url}{review.id}/"
        resp = client.put(url, {"rating": 1, "review_text": "Hacked!"}, format="json")
        assert resp.status_code == status.HTTP_404_NOT_FOUND


# ──────────────────────────────────────────────
# Public: Course Reviews
# ──────────────────────────────────────────────


@pytest.mark.django_db
class TestPublicReviews:
    url = f"{BASE}/public/"

    def test_list_published_reviews(self, api_client, review):
        resp = api_client.get(self.url)
        assert resp.status_code == status.HTTP_200_OK

    def test_filter_by_course(self, api_client, course, review):
        resp = api_client.get(f"{self.url}?course={course.id}")
        assert resp.status_code == status.HTTP_200_OK

    def test_rejected_reviews_not_shown(self, api_client, enrolled_student, course):
        ReviewFactory(
            student=enrolled_student, course=course,
            rating=1, status=Review.Status.REJECTED,
        )
        resp = api_client.get(f"{self.url}?course={course.id}")
        assert resp.status_code == status.HTTP_200_OK
        results = resp.data.get("results", resp.data.get("data", []))
        for r in results:
            assert r["status"] != "rejected"

    def test_retrieve_single_review(self, api_client, review):
        url = f"{self.url}{review.id}/"
        resp = api_client.get(url)
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data["data"]["id"] == str(review.id)


# ──────────────────────────────────────────────
# Instructor: Review Response
# ──────────────────────────────────────────────


@pytest.mark.django_db
class TestInstructorReviewResponse:
    url = f"{BASE}/instructor/"

    def test_list_course_reviews(self, api_client, instructor, course, review):
        client = auth(api_client, instructor)
        resp = client.get(self.url)
        assert resp.status_code == status.HTTP_200_OK

    def test_respond_to_review(self, api_client, instructor, review):
        client = auth(api_client, instructor)
        data = {
            "review_id": str(review.id),
            "response_text": "Thank you for your feedback!",
        }
        resp = client.post(f"{self.url}respond/", data, format="json")
        assert resp.status_code == status.HTTP_201_CREATED
        assert ReviewResponse.objects.filter(review=review).exists()

    def test_cannot_respond_to_other_instructor_course(self, api_client, review):
        other_instructor = InstructorFactory()
        client = auth(api_client, other_instructor)
        data = {
            "review_id": str(review.id),
            "response_text": "I shouldn't be able to do this.",
        }
        resp = client.post(f"{self.url}respond/", data, format="json")
        assert resp.status_code == status.HTTP_403_FORBIDDEN

    def test_respond_updates_existing_response(self, api_client, instructor, review):
        ReviewResponseFactory(review=review, instructor=instructor)
        client = auth(api_client, instructor)
        data = {
            "review_id": str(review.id),
            "response_text": "Updated response.",
        }
        resp = client.post(f"{self.url}respond/", data, format="json")
        assert resp.status_code == status.HTTP_201_CREATED
        assert ReviewResponse.objects.filter(review=review).count() == 1

    def test_student_cannot_access_instructor_endpoint(self, api_client, student):
        client = auth(api_client, student)
        resp = client.get(self.url)
        assert resp.status_code == status.HTTP_403_FORBIDDEN


# ──────────────────────────────────────────────
# Admin: Review Moderation
# ──────────────────────────────────────────────


@pytest.mark.django_db
class TestAdminReviewModeration:
    url = f"{BASE}/admin/"

    def test_list_all_reviews(self, api_client, admin, review):
        client = auth(api_client, admin)
        resp = client.get(self.url)
        assert resp.status_code == status.HTTP_200_OK

    def test_filter_reviews_by_status(self, api_client, admin, review):
        client = auth(api_client, admin)
        resp = client.get(f"{self.url}?status=published")
        assert resp.status_code == status.HTTP_200_OK

    def test_moderate_reject_review(self, api_client, admin, review, course):
        client = auth(api_client, admin)
        url = f"{self.url}{review.id}/moderate/"
        resp = client.put(url, {"status": "rejected"}, format="json")
        assert resp.status_code == status.HTTP_200_OK
        review.refresh_from_db()
        assert review.status == Review.Status.REJECTED
        # Rejected review should not count in course rating
        course.refresh_from_db()
        assert course.rating_count == 0

    def test_moderate_publish_review(self, api_client, admin, course):
        rev = ReviewFactory(
            student=UserFactory(), course=course,
            rating=5, status=Review.Status.PENDING,
        )
        client = auth(api_client, admin)
        url = f"{self.url}{rev.id}/moderate/"
        resp = client.put(url, {"status": "published"}, format="json")
        assert resp.status_code == status.HTTP_200_OK
        rev.refresh_from_db()
        assert rev.status == Review.Status.PUBLISHED

    def test_student_cannot_access_admin_endpoint(self, api_client, student):
        client = auth(api_client, student)
        resp = client.get(self.url)
        assert resp.status_code == status.HTTP_403_FORBIDDEN

    def test_instructor_cannot_access_admin_endpoint(self, api_client, instructor):
        client = auth(api_client, instructor)
        resp = client.get(self.url)
        assert resp.status_code == status.HTTP_403_FORBIDDEN


# ──────────────────────────────────────────────
# Course Rating Aggregation
# ──────────────────────────────────────────────


@pytest.mark.django_db
class TestCourseRatingAggregation:
    url = f"{BASE}/student/"

    def test_multiple_reviews_average(self, api_client, course, enrolled_student, enrolled_student2):
        ReviewFactory(student=enrolled_student, course=course, rating=5)
        ReviewFactory(student=enrolled_student2, course=course, rating=3)
        from apps.reviews.services.review_service import ReviewService
        ReviewService._refresh_course_rating(course)
        course.refresh_from_db()
        assert course.average_rating == Decimal("4.00")
        assert course.rating_count == 2

    def test_rating_zero_when_no_reviews(self, api_client, course):
        from apps.reviews.services.review_service import ReviewService
        ReviewService._refresh_course_rating(course)
        course.refresh_from_db()
        assert course.average_rating == Decimal("0.00")
        assert course.rating_count == 0
