import pytest
from rest_framework import status

from apps.courses.models import Category, Course, Language, Level
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
        results = response.data["data"]["results"]
        assert len(results) == 1
        assert results[0]["status"] == Course.Status.PUBLISHED

    def test_draft_courses_not_visible(self, api_client):
        CourseFactory(status=Course.Status.DRAFT)

        response = api_client.get(f"{BASE}/")

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["data"]["results"]) == 0

    def test_supports_pagination(self, api_client):
        for _ in range(5):
            CourseFactory(status=Course.Status.PUBLISHED)

        response = api_client.get(f"{BASE}/", {"page_size": 2})

        assert response.status_code == status.HTTP_200_OK
        assert "count" in response.data["data"]
        assert "next" in response.data["data"]
        assert len(response.data["data"]["results"]) == 2

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
        assert len(response.data["data"]["results"]) == 1
        assert response.data["data"]["results"][0]["category"]["slug"] == cat1.slug

    def test_filter_by_is_free(self, api_client):
        CourseFactory(status=Course.Status.PUBLISHED, is_free=True)
        CourseFactory(status=Course.Status.PUBLISHED, is_free=False)

        response = api_client.get(f"{BASE}/", {"is_free": "true"})

        assert response.status_code == status.HTTP_200_OK
        assert all(c["is_free"] for c in response.data["data"]["results"])

    def test_search_by_title(self, api_client):
        CourseFactory(title="Django Mastery", status=Course.Status.PUBLISHED)
        CourseFactory(title="React Fundamentals", status=Course.Status.PUBLISHED)

        response = api_client.get(f"{BASE}/", {"search": "Django"})

        assert response.status_code == status.HTTP_200_OK
        results = response.data["data"]["results"]
        assert len(results) == 1
        assert results[0]["title"] == "Django Mastery"

    def test_ordering_by_created_at(self, api_client):
        CourseFactory(status=Course.Status.PUBLISHED)
        CourseFactory(status=Course.Status.PUBLISHED)

        response = api_client.get(f"{BASE}/", {"ordering": "created_at"})

        assert response.status_code == status.HTTP_200_OK
        results = response.data["data"]["results"]
        assert len(results) == 2

    def test_ordering_by_average_rating_descending(self, api_client):
        CourseFactory(status=Course.Status.PUBLISHED, average_rating=4.5)
        CourseFactory(status=Course.Status.PUBLISHED, average_rating=3.0)

        response = api_client.get(f"{BASE}/", {"ordering": "-average_rating"})

        assert response.status_code == status.HTTP_200_OK
        results = response.data["data"]["results"]
        assert float(results[0]["average_rating"]) >= float(results[1]["average_rating"])

    def test_response_contains_expected_fields(self, api_client):
        CourseFactory(status=Course.Status.PUBLISHED)

        response = api_client.get(f"{BASE}/")

        assert response.status_code == status.HTTP_200_OK
        course_data = response.data["data"]["results"][0]
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
        assert response.data["data"]["slug"] == course.slug
        assert response.data["data"]["title"] == "Detail Course"

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
        assert len(response.data["data"]["learning_outcomes"]) == 1

    def test_detail_response_includes_requirements(self, api_client):
        from tests.factories import RequirementFactory

        course = CourseFactory(status=Course.Status.PUBLISHED)
        RequirementFactory(course=course, text="Know Python")

        response = api_client.get(f"{BASE}/{course.slug}/")

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["data"]["requirements"]) == 1

    def test_detail_includes_instructor_info(self, api_client):
        instructor = InstructorFactory(first_name="John", last_name="Doe")
        course = CourseFactory(
            instructor=instructor, status=Course.Status.PUBLISHED
        )

        response = api_client.get(f"{BASE}/{course.slug}/")

        assert response.status_code == status.HTTP_200_OK
        assert response.data["data"]["instructor_name"] == "John Doe"


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
        assert response.data["data"]["title"] == "New Instructor Course"

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
        assert response.data["data"]["count"] == 2

    def test_admin_sees_all_courses_in_instructor_list(
        self, admin_client
    ):
        instructor1 = InstructorFactory()
        instructor2 = InstructorFactory()
        CourseFactory(instructor=instructor1)
        CourseFactory(instructor=instructor2)

        response = admin_client.get(self.INSTRUCTOR_URL)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["data"]["count"] == 2

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
        assert str(response.data["data"]["id"]) == str(course.id)

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
        assert response.data["data"]["status"] == Course.Status.DRAFT


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
            instructor=instructor_user,
            status=Course.Status.DRAFT,
            thumbnail="https://example.com/thumb.jpg",
        )

        api_client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {access_token_for_user(instructor_user)}"
        )
        response = api_client.post(
            f"{self.INSTRUCTOR_URL}{course.id}/publish/",
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
        response = api_client.post(
            f"{self.INSTRUCTOR_URL}{course.id}/archive/",
        )

        assert response.status_code == status.HTTP_200_OK
        course.refresh_from_db()
        assert course.status == Course.Status.ARCHIVED

    def test_published_course_visible_in_public_list(self, api_client, instructor_user):
        CourseFactory(instructor=instructor_user, status=Course.Status.PUBLISHED)

        response = api_client.get(f"{BASE}/")

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["data"]["results"]) == 1

    def test_archived_course_not_visible_in_public_list(self, api_client, instructor_user):
        CourseFactory(instructor=instructor_user, status=Course.Status.ARCHIVED)

        response = api_client.get(f"{BASE}/")

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["data"]["results"]) == 0
