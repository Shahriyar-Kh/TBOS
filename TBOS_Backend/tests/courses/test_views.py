<<<<<<< HEAD
"""Tests for courses views and API endpoints."""
=======
>>>>>>> 36e9d9d1ebb34bf8b78a481d28bf7cf2ca6f757e
import pytest
from rest_framework import status

from apps.courses.models import Category, Course, Language, Level
<<<<<<< HEAD


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
=======
from tests.factories import (
    CategoryFactory,
    CourseFactory,
    InstructorFactory,
    LanguageFactory,
    LevelFactory,
)

BASE = "/api/v1/courses"


# ──────────────────────────────────────────────
# Public course list
# ──────────────────────────────────────────────
@pytest.mark.django_db
class TestPublicCourseListView:
    def test_returns_only_published_courses(self, api_client):
        CourseFactory(status=Course.Status.PUBLISHED)
        CourseFactory(status=Course.Status.DRAFT)
        CourseFactory(status=Course.Status.ARCHIVED)

        response = api_client.get(f"{BASE}/")

        assert response.status_code == status.HTTP_200_OK
        results = response.data["results"]
        assert len(results) == 1
        assert results[0]["status"] == Course.Status.PUBLISHED

    def test_draft_courses_not_visible(self, api_client):
        CourseFactory(status=Course.Status.DRAFT)

        response = api_client.get(f"{BASE}/")

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 0

    def test_supports_pagination(self, api_client):
        for _ in range(5):
            CourseFactory(status=Course.Status.PUBLISHED)

        response = api_client.get(f"{BASE}/", {"page_size": 2})

        assert response.status_code == status.HTTP_200_OK
        assert "count" in response.data
        assert "next" in response.data
        assert len(response.data["results"]) == 2

    def test_accessible_without_authentication(self, api_client):
        CourseFactory(status=Course.Status.PUBLISHED)

        response = api_client.get(f"{BASE}/")

        assert response.status_code == status.HTTP_200_OK

    def test_filter_by_category_slug(self, api_client):
        cat1 = CategoryFactory(name="Filter Cat A")
        cat2 = CategoryFactory(name="Filter Cat B")
        CourseFactory(status=Course.Status.PUBLISHED, category=cat1)
        CourseFactory(status=Course.Status.PUBLISHED, category=cat2)

        response = api_client.get(f"{BASE}/", {"category__slug": cat1.slug})

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1
        assert response.data["results"][0]["category"]["slug"] == cat1.slug

    def test_filter_by_is_free(self, api_client):
        CourseFactory(status=Course.Status.PUBLISHED, is_free=True)
        CourseFactory(status=Course.Status.PUBLISHED, is_free=False)

        response = api_client.get(f"{BASE}/", {"is_free": "true"})

        assert response.status_code == status.HTTP_200_OK
        assert all(c["is_free"] for c in response.data["results"])

    def test_search_by_title(self, api_client):
        CourseFactory(title="Django Mastery", status=Course.Status.PUBLISHED)
        CourseFactory(title="React Fundamentals", status=Course.Status.PUBLISHED)

        response = api_client.get(f"{BASE}/", {"search": "Django"})

        assert response.status_code == status.HTTP_200_OK
        results = response.data["results"]
        assert len(results) == 1
        assert results[0]["title"] == "Django Mastery"

    def test_ordering_by_created_at(self, api_client):
        CourseFactory(status=Course.Status.PUBLISHED)
        CourseFactory(status=Course.Status.PUBLISHED)

        response = api_client.get(f"{BASE}/", {"ordering": "created_at"})

        assert response.status_code == status.HTTP_200_OK
        results = response.data["results"]
        assert len(results) == 2

    def test_ordering_by_average_rating_descending(self, api_client):
        CourseFactory(status=Course.Status.PUBLISHED, average_rating=4.5)
        CourseFactory(status=Course.Status.PUBLISHED, average_rating=3.0)

        response = api_client.get(f"{BASE}/", {"ordering": "-average_rating"})

        assert response.status_code == status.HTTP_200_OK
        results = response.data["results"]
        assert float(results[0]["average_rating"]) >= float(results[1]["average_rating"])

    def test_response_contains_expected_fields(self, api_client):
        CourseFactory(status=Course.Status.PUBLISHED)

        response = api_client.get(f"{BASE}/")

        assert response.status_code == status.HTTP_200_OK
        course_data = response.data["results"][0]
        for field in ["id", "title", "slug", "price", "status", "instructor_name"]:
            assert field in course_data


# ──────────────────────────────────────────────
# Public course detail
# ──────────────────────────────────────────────
@pytest.mark.django_db
class TestPublicCourseDetailView:
    def test_returns_published_course_by_slug(self, api_client):
        course = CourseFactory(
            title="Detail Course", status=Course.Status.PUBLISHED
        )

        response = api_client.get(f"{BASE}/{course.slug}/")

        assert response.status_code == status.HTTP_200_OK
        assert response.data["slug"] == course.slug
        assert response.data["title"] == "Detail Course"

    def test_returns_404_for_invalid_slug(self, api_client):
        response = api_client.get(f"{BASE}/nonexistent-slug/")

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_draft_course_not_accessible_publicly(self, api_client):
        course = CourseFactory(status=Course.Status.DRAFT)

        response = api_client.get(f"{BASE}/{course.slug}/")

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_detail_response_includes_learning_outcomes(self, api_client):
        from tests.factories import LearningOutcomeFactory

        course = CourseFactory(status=Course.Status.PUBLISHED)
        LearningOutcomeFactory(course=course, text="Learn DRF")

        response = api_client.get(f"{BASE}/{course.slug}/")

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["learning_outcomes"]) == 1

    def test_detail_response_includes_requirements(self, api_client):
        from tests.factories import RequirementFactory

        course = CourseFactory(status=Course.Status.PUBLISHED)
        RequirementFactory(course=course, text="Know Python")

        response = api_client.get(f"{BASE}/{course.slug}/")

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["requirements"]) == 1

    def test_detail_includes_instructor_info(self, api_client):
        instructor = InstructorFactory(first_name="John", last_name="Doe")
        course = CourseFactory(
            instructor=instructor, status=Course.Status.PUBLISHED
        )

        response = api_client.get(f"{BASE}/{course.slug}/")

        assert response.status_code == status.HTTP_200_OK
        assert response.data["instructor_name"] == "John Doe"
        assert "instructor_id" in response.data


# ──────────────────────────────────────────────
# Category / Level / Language public list views
# ──────────────────────────────────────────────
@pytest.mark.django_db
class TestPublicReferenceListViews:
    def test_category_list_accessible_without_auth(self, api_client):
        CategoryFactory(name="View Cat 1")

        response = api_client.get(f"{BASE}/categories/")

        assert response.status_code == status.HTTP_200_OK
        assert isinstance(response.data, list)

    def test_level_list_accessible_without_auth(self, api_client):
        LevelFactory(name="Beginner View")

        response = api_client.get(f"{BASE}/levels/")

        assert response.status_code == status.HTTP_200_OK
        assert isinstance(response.data, list)

    def test_language_list_accessible_without_auth(self, api_client):
        LanguageFactory(name="English View")

        response = api_client.get(f"{BASE}/languages/")

        assert response.status_code == status.HTTP_200_OK
        assert isinstance(response.data, list)

    def test_category_list_has_no_pagination(self, api_client):
        for i in range(25):
            CategoryFactory(name=f"Pagination Cat {i}")

        response = api_client.get(f"{BASE}/categories/")

        assert response.status_code == status.HTTP_200_OK
        assert isinstance(response.data, list)
        assert len(response.data) >= 25


# ──────────────────────────────────────────────
# Instructor course ViewSet
# ──────────────────────────────────────────────
@pytest.mark.django_db
class TestInstructorCourseViewSet:
    INSTRUCTOR_URL = f"{BASE}/instructor/courses/"

    def test_instructor_can_create_course(
        self, instructor_client, instructor_user
    ):
        category = CategoryFactory(name="Instructor Create Cat")

        response = instructor_client.post(
            self.INSTRUCTOR_URL,
            {
                "title": "New Instructor Course",
                "description": "Course by instructor",
                "category_id": str(category.id),
            },
            format="json",
        )

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["title"] == "New Instructor Course"

    def test_student_cannot_create_course(self, auth_client):
        category = CategoryFactory(name="Student Create Cat")

        response = auth_client.post(
            self.INSTRUCTOR_URL,
            {
                "title": "Student Course Attempt",
                "description": "Should fail",
                "category_id": str(category.id),
            },
            format="json",
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_unauthenticated_user_cannot_create_course(self, api_client):
        category = CategoryFactory(name="Unauth Create Cat")

        response = api_client.post(
            self.INSTRUCTOR_URL,
            {
                "title": "Unauth Course",
                "description": "Should fail",
                "category_id": str(category.id),
            },
            format="json",
        )

        assert response.status_code in {
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
        }

    def test_instructor_can_list_own_courses(
        self, api_client, instructor_user, access_token_for_user
    ):
        CourseFactory(instructor=instructor_user)
        CourseFactory(instructor=instructor_user)
        other_instructor = InstructorFactory()
        CourseFactory(instructor=other_instructor)

        api_client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {access_token_for_user(instructor_user)}"
        )
        response = api_client.get(self.INSTRUCTOR_URL)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 2

    def test_admin_sees_all_courses_in_instructor_list(
        self, admin_client
    ):
        instructor1 = InstructorFactory()
        instructor2 = InstructorFactory()
        CourseFactory(instructor=instructor1)
        CourseFactory(instructor=instructor2)

        response = admin_client.get(self.INSTRUCTOR_URL)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 2

    def test_instructor_can_update_own_course(
        self, api_client, instructor_user, access_token_for_user
    ):
        course = CourseFactory(instructor=instructor_user)
        category = CategoryFactory(name="Update Cat")

        api_client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {access_token_for_user(instructor_user)}"
        )
        response = api_client.patch(
            f"{self.INSTRUCTOR_URL}{course.id}/",
            {"title": "Updated Title"},
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK

    def test_instructor_cannot_update_others_course(
        self, api_client, access_token_for_user
    ):
        owner = InstructorFactory()
        other_instructor = InstructorFactory()
        course = CourseFactory(instructor=owner)
        category = CategoryFactory(name="Other Update Cat")

        api_client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {access_token_for_user(other_instructor)}"
        )
        response = api_client.patch(
            f"{self.INSTRUCTOR_URL}{course.id}/",
            {"title": "Should Fail"},
            format="json",
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_instructor_can_retrieve_own_course(
        self, api_client, instructor_user, access_token_for_user
    ):
        course = CourseFactory(instructor=instructor_user)

        api_client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {access_token_for_user(instructor_user)}"
        )
        response = api_client.get(f"{self.INSTRUCTOR_URL}{course.id}/")

        assert response.status_code == status.HTTP_200_OK
        assert str(response.data["id"]) == str(course.id)

    def test_instructor_can_delete_own_course(
        self, api_client, instructor_user, access_token_for_user
    ):
        course = CourseFactory(instructor=instructor_user)

        api_client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {access_token_for_user(instructor_user)}"
        )
        response = api_client.delete(f"{self.INSTRUCTOR_URL}{course.id}/")

        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not Course.objects.filter(pk=course.pk).exists()

    def test_course_creation_sets_default_status_draft(
        self, instructor_client, instructor_user
    ):
        category = CategoryFactory(name="Draft Status Cat")

        response = instructor_client.post(
            self.INSTRUCTOR_URL,
            {
                "title": "Draft New Course",
                "description": "desc",
                "category_id": str(category.id),
            },
            format="json",
        )

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["status"] == Course.Status.DRAFT


# ──────────────────────────────────────────────
# Admin category ViewSet
# ──────────────────────────────────────────────
@pytest.mark.django_db
class TestAdminCategoryViewSet:
    ADMIN_CAT_URL = f"{BASE}/admin/categories/"

    def test_admin_can_list_categories(self, admin_client):
        CategoryFactory(name="Admin List Cat 1")

        response = admin_client.get(self.ADMIN_CAT_URL)

        assert response.status_code == status.HTTP_200_OK

    def test_admin_can_create_category(self, admin_client):
        response = admin_client.post(
            self.ADMIN_CAT_URL,
            {"name": "New Admin Category", "icon": "fa-code"},
            format="json",
        )

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["name"] == "New Admin Category"
        assert Category.objects.filter(name="New Admin Category").exists()

    def test_admin_can_update_category(self, admin_client):
        category = CategoryFactory(name="Old Name")

        response = admin_client.patch(
            f"{self.ADMIN_CAT_URL}{category.id}/",
            {"name": "New Name"},
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK
        category.refresh_from_db()
        assert category.name == "New Name"

    def test_admin_can_delete_category(self, admin_client):
        category = CategoryFactory(name="Delete Me Cat")

        response = admin_client.delete(f"{self.ADMIN_CAT_URL}{category.id}/")

        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not Category.objects.filter(pk=category.pk).exists()

    def test_instructor_cannot_access_admin_categories(self, instructor_client):
        response = instructor_client.get(self.ADMIN_CAT_URL)

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_student_cannot_access_admin_categories(self, auth_client):
        response = auth_client.get(self.ADMIN_CAT_URL)

        assert response.status_code == status.HTTP_403_FORBIDDEN


# ──────────────────────────────────────────────
# Admin level ViewSet
# ──────────────────────────────────────────────
@pytest.mark.django_db
class TestAdminLevelViewSet:
    ADMIN_LEVEL_URL = f"{BASE}/admin/levels/"

    def test_admin_can_create_level(self, admin_client):
        response = admin_client.post(
            self.ADMIN_LEVEL_URL,
            {"name": "Advanced Level"},
            format="json",
        )

        assert response.status_code == status.HTTP_201_CREATED
        assert Level.objects.filter(name="Advanced Level").exists()

    def test_admin_can_delete_level(self, admin_client):
        level = LevelFactory(name="Delete Me Level")

        response = admin_client.delete(f"{self.ADMIN_LEVEL_URL}{level.id}/")

        assert response.status_code == status.HTTP_204_NO_CONTENT

    def test_non_admin_cannot_create_level(self, auth_client):
        response = auth_client.post(
            self.ADMIN_LEVEL_URL,
            {"name": "Unauthorized Level"},
            format="json",
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN


# ──────────────────────────────────────────────
# Admin language ViewSet
# ──────────────────────────────────────────────
@pytest.mark.django_db
class TestAdminLanguageViewSet:
    ADMIN_LANG_URL = f"{BASE}/admin/languages/"

    def test_admin_can_create_language(self, admin_client):
        response = admin_client.post(
            self.ADMIN_LANG_URL,
            {"name": "Spanish"},
            format="json",
        )

        assert response.status_code == status.HTTP_201_CREATED
        assert Language.objects.filter(name="Spanish").exists()

    def test_admin_can_delete_language(self, admin_client):
        language = LanguageFactory(name="Delete Me Lang")

        response = admin_client.delete(f"{self.ADMIN_LANG_URL}{language.id}/")

        assert response.status_code == status.HTTP_204_NO_CONTENT

    def test_non_admin_cannot_create_language(self, auth_client):
        response = auth_client.post(
            self.ADMIN_LANG_URL,
            {"name": "Unauthorized Language"},
            format="json",
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN


# ──────────────────────────────────────────────
# Course status workflow
# ──────────────────────────────────────────────
@pytest.mark.django_db
class TestCourseStatusWorkflow:
    INSTRUCTOR_URL = f"{BASE}/instructor/courses/"

    def test_instructor_can_publish_course_via_update(
        self, api_client, instructor_user, access_token_for_user
    ):
        course = CourseFactory(
            instructor=instructor_user, status=Course.Status.DRAFT
        )

        api_client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {access_token_for_user(instructor_user)}"
        )
        response = api_client.patch(
            f"{self.INSTRUCTOR_URL}{course.id}/",
            {"status": Course.Status.PUBLISHED},
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK
        course.refresh_from_db()
        assert course.status == Course.Status.PUBLISHED

    def test_instructor_can_archive_course_via_update(
        self, api_client, instructor_user, access_token_for_user
    ):
        course = CourseFactory(
            instructor=instructor_user, status=Course.Status.PUBLISHED
        )

        api_client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {access_token_for_user(instructor_user)}"
        )
        response = api_client.patch(
            f"{self.INSTRUCTOR_URL}{course.id}/",
            {"status": Course.Status.ARCHIVED},
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK
        course.refresh_from_db()
        assert course.status == Course.Status.ARCHIVED

    def test_published_course_visible_in_public_list(self, api_client, instructor_user):
        CourseFactory(instructor=instructor_user, status=Course.Status.PUBLISHED)

        response = api_client.get(f"{BASE}/")

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1

    def test_archived_course_not_visible_in_public_list(self, api_client, instructor_user):
        CourseFactory(instructor=instructor_user, status=Course.Status.ARCHIVED)

        response = api_client.get(f"{BASE}/")

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 0
>>>>>>> 36e9d9d1ebb34bf8b78a481d28bf7cf2ca6f757e
