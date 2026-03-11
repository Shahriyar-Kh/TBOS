"""Tests for courses views and API endpoints."""
import pytest
from rest_framework import status

from apps.courses.models import Category, Course, Language, Level


@pytest.fixture
def category(db):
    return Category.objects.create(name="Technology")


@pytest.fixture
def level(db):
    return Level.objects.create(name="Intermediate")


@pytest.fixture
def language(db):
    return Language.objects.create(name="English")


@pytest.fixture
def published_course(db, instructor_user, category, level, language):
    return Course.objects.create(
        title="Published Python Course",
        description="A great Python course",
        instructor=instructor_user,
        category=category,
        level=level,
        language=language,
        thumbnail="https://example.com/thumb.jpg",
        price="49.99",
        status=Course.Status.PUBLISHED,
    )


@pytest.fixture
def draft_course(db, instructor_user, category, level):
    return Course.objects.create(
        title="Draft Django Course",
        description="A draft course",
        instructor=instructor_user,
        category=category,
        level=level,
        thumbnail="https://example.com/thumb2.jpg",
        price="39.99",
        status=Course.Status.DRAFT,
    )


# ── Public endpoints ───────────────────────────────────────────

class TestPublicCourseList:
    def test_list_returns_only_published(self, api_client, published_course, draft_course):
        response = api_client.get("/api/v1/courses/")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["success"] is True
        results = response.data["data"]["results"]
        titles = [r["title"] for r in results]
        assert "Published Python Course" in titles
        assert "Draft Django Course" not in titles

    def test_list_accessible_without_auth(self, api_client, published_course):
        response = api_client.get("/api/v1/courses/")
        assert response.status_code == status.HTTP_200_OK

    def test_search_by_title(self, api_client, published_course):
        response = api_client.get("/api/v1/courses/?search=Python")
        assert response.status_code == status.HTTP_200_OK
        results = response.data["data"]["results"]
        assert any("Python" in r["title"] for r in results)

    def test_filter_by_category_slug(self, api_client, published_course):
        response = api_client.get(
            f"/api/v1/courses/?category__slug={published_course.category.slug}"
        )
        assert response.status_code == status.HTTP_200_OK

    def test_ordering_by_newest(self, api_client, published_course):
        response = api_client.get("/api/v1/courses/?ordering=-created_at")
        assert response.status_code == status.HTTP_200_OK


class TestPublicCourseDetail:
    def test_returns_published_course_by_slug(self, api_client, published_course):
        response = api_client.get(f"/api/v1/courses/{published_course.slug}/")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["data"]["title"] == "Published Python Course"

    def test_draft_course_not_accessible(self, api_client, draft_course):
        response = api_client.get(f"/api/v1/courses/{draft_course.slug}/")
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_nonexistent_slug_returns_404(self, api_client, db):
        response = api_client.get("/api/v1/courses/nonexistent-course/")
        assert response.status_code == status.HTTP_404_NOT_FOUND


# ── Instructor endpoints ───────────────────────────────────────

class TestInstructorCourseCreate:
    def test_instructor_can_create_course(
        self, instructor_client, instructor_user, category, level
    ):
        data = {
            "title": "New Instructor Course",
            "description": "A detailed course description here.",
            "category_id": str(category.id),
            "level_id": str(level.id),
            "price": "59.99",
        }
        response = instructor_client.post(
            "/api/v1/courses/instructor/courses/", data, format="json"
        )
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["success"] is True
        assert response.data["data"]["status"] == "draft"

    def test_student_cannot_create_course(self, auth_client, category):
        data = {
            "title": "Unauthorized Course",
            "description": "Should not be created.",
            "category_id": str(category.id),
            "price": "0",
        }
        response = auth_client.post(
            "/api/v1/courses/instructor/courses/", data, format="json"
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_unauthenticated_cannot_create_course(self, api_client, category):
        data = {
            "title": "Anon Course",
            "description": "Should fail.",
            "category_id": str(category.id),
            "price": "0",
        }
        response = api_client.post(
            "/api/v1/courses/instructor/courses/", data, format="json"
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_title_min_length_validation(self, instructor_client, category):
        data = {
            "title": "Hi",  # too short
            "description": "A course.",
            "category_id": str(category.id),
            "price": "0",
        }
        response = instructor_client.post(
            "/api/v1/courses/instructor/courses/", data, format="json"
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_price_cannot_be_negative(self, instructor_client, category):
        data = {
            "title": "Negative Price Course",
            "description": "This should fail.",
            "category_id": str(category.id),
            "price": "-10.00",
        }
        response = instructor_client.post(
            "/api/v1/courses/instructor/courses/", data, format="json"
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_discount_price_must_be_less_than_price(self, instructor_client, category):
        data = {
            "title": "Invalid Discount Course",
            "description": "Discount >= price is invalid.",
            "category_id": str(category.id),
            "price": "50.00",
            "discount_price": "60.00",
        }
        response = instructor_client.post(
            "/api/v1/courses/instructor/courses/", data, format="json"
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST


class TestInstructorCourseList:
    def test_instructor_sees_only_own_courses(
        self, instructor_client, instructor_user, draft_course, db
    ):
        from tests.factories import InstructorFactory
        other = InstructorFactory()
        Category.objects.get_or_create(name="Other")
        response = instructor_client.get("/api/v1/courses/instructor/courses/")
        assert response.status_code == status.HTTP_200_OK
        for course_data in response.data["data"]["results"]:
            assert course_data["instructor_name"] == instructor_user.full_name


class TestInstructorCourseUpdate:
    def test_instructor_can_update_own_course(
        self, instructor_client, draft_course
    ):
        response = instructor_client.put(
            f"/api/v1/courses/instructor/courses/{draft_course.id}/",
            {"title": "Updated Draft Course", "description": "Updated description here."},
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data["data"]["title"] == "Updated Draft Course"

    def test_instructor_cannot_update_others_course(
        self, db, published_course
    ):
        from tests.factories import InstructorFactory
        from rest_framework_simplejwt.tokens import RefreshToken
        from rest_framework.test import APIClient

        other = InstructorFactory()
        token = str(RefreshToken.for_user(other).access_token)
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        response = client.put(
            f"/api/v1/courses/instructor/courses/{published_course.id}/",
            {"title": "Hijacked Title", "description": "Should fail."},
            format="json",
        )
        assert response.status_code in (status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND)


class TestInstructorPublishCourse:
    def test_instructor_can_publish_complete_course(
        self, instructor_client, draft_course
    ):
        response = instructor_client.post(
            f"/api/v1/courses/instructor/courses/{draft_course.id}/publish/"
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data["data"]["status"] == "published"

    def test_publish_fails_for_incomplete_course(self, instructor_client, db, instructor_user, category):
        course = Course.objects.create(
            title="Incomplete",
            description="No level or thumbnail",
            instructor=instructor_user,
            category=category,
            price="0",
        )
        response = instructor_client.post(
            f"/api/v1/courses/instructor/courses/{course.id}/publish/"
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST


# ── Admin endpoints ────────────────────────────────────────────

class TestAdminCourseList:
    def test_admin_can_list_all_courses(
        self, admin_client, draft_course, published_course
    ):
        response = admin_client.get("/api/v1/courses/admin/courses/")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["data"]["count"] >= 2

    def test_non_admin_cannot_access_admin_list(self, instructor_client):
        response = instructor_client.get("/api/v1/courses/admin/courses/")
        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestAdminPublishCourse:
    def test_admin_can_publish_any_course(self, admin_client, draft_course):
        response = admin_client.put(
            f"/api/v1/courses/admin/courses/{draft_course.id}/publish/"
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data["data"]["status"] == "published"


class TestAdminDeleteCourse:
    def test_admin_can_delete_course(self, admin_client, draft_course):
        course_id = draft_course.id
        response = admin_client.delete(
            f"/api/v1/courses/admin/courses/{course_id}/"
        )
        assert response.status_code == status.HTTP_200_OK
        assert not Course.objects.filter(pk=course_id).exists()

    def test_non_admin_cannot_delete_course(self, instructor_client, draft_course):
        response = instructor_client.delete(
            f"/api/v1/courses/admin/courses/{draft_course.id}/"
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN
