import pytest
from rest_framework import status

from apps.courses.models import Category, Course, Language, Level
from tests.factories import AdminFactory, InstructorFactory, UserFactory


def assert_success(payload):
    assert payload["success"] is True
    assert "data" in payload
    assert "message" in payload


def assert_error(payload):
    assert payload["success"] is False


@pytest.fixture
def category(db):
    return Category.objects.create(name="Web Development")


@pytest.fixture
def level(db):
    return Level.objects.create(name="Beginner")


@pytest.fixture
def language(db):
    return Language.objects.create(name="English")


@pytest.fixture
def published_course(db, category, level):
    instructor = InstructorFactory()
    return Course.objects.create(
        title="Published Course For Test",
        description="Full description here",
        instructor=instructor,
        category=category,
        level=level,
        featured_image="https://example.com/img.jpg",
        status=Course.Status.PUBLISHED,
    )


@pytest.fixture
def draft_course(db, category, level, instructor_user):
    return Course.objects.create(
        title="Draft Course For Instructor",
        description="Draft description",
        instructor=instructor_user,
        category=category,
        level=level,
        featured_image="https://example.com/img.jpg",
    )


@pytest.mark.django_db
class TestPublicCourseListView:
    def test_lists_only_published_courses(self, api_client, published_course):
        resp = api_client.get("/api/v1/courses/")
        assert resp.status_code == status.HTTP_200_OK
        assert_success(resp.data)

    def test_draft_courses_not_visible(self, api_client, category, level):
        instructor = InstructorFactory()
        Course.objects.create(
            title="Hidden Draft Course",
            description="desc",
            instructor=instructor,
            status=Course.Status.DRAFT,
        )
        resp = api_client.get("/api/v1/courses/")
        assert resp.status_code == status.HTTP_200_OK
        results = resp.data["data"]["results"]
        titles = [c["title"] for c in results]
        assert "Hidden Draft Course" not in titles

    def test_search_by_title(self, api_client, published_course):
        resp = api_client.get("/api/v1/courses/?search=Published+Course")
        assert resp.status_code == status.HTTP_200_OK
        results = resp.data["data"]["results"]
        assert any("Published Course" in c["title"] for c in results)

    def test_filter_by_category_slug(self, api_client, published_course, category):
        resp = api_client.get(f"/api/v1/courses/?category__slug={category.slug}")
        assert resp.status_code == status.HTTP_200_OK

    def test_unauthenticated_access_allowed(self, api_client, published_course):
        resp = api_client.get("/api/v1/courses/")
        assert resp.status_code == status.HTTP_200_OK


@pytest.mark.django_db
class TestPublicCourseDetailView:
    def test_retrieve_published_course(self, api_client, published_course):
        resp = api_client.get(f"/api/v1/courses/{published_course.slug}/")
        assert resp.status_code == status.HTTP_200_OK
        assert_success(resp.data)
        assert resp.data["data"]["slug"] == published_course.slug

    def test_draft_course_not_accessible(self, api_client, category, level):
        instructor = InstructorFactory()
        draft = Course.objects.create(
            title="A Hidden Draft Here",
            description="desc",
            instructor=instructor,
            status=Course.Status.DRAFT,
        )
        resp = api_client.get(f"/api/v1/courses/{draft.slug}/")
        assert resp.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
class TestCategoryListView:
    def test_lists_categories(self, api_client, category):
        resp = api_client.get("/api/v1/courses/categories/")
        assert resp.status_code == status.HTTP_200_OK
        assert_success(resp.data)
        names = [c["name"] for c in resp.data["data"]]
        assert "Web Development" in names


@pytest.mark.django_db
class TestInstructorCourseViewSet:
    def test_instructor_can_create_course(self, instructor_client, instructor_user, category, level):
        resp = instructor_client.post(
            "/api/v1/courses/instructor/courses/",
            {
                "title": "Learning Django REST Framework",
                "description": "A comprehensive guide",
                "category_id": str(category.id),
                "level_id": str(level.id),
                "price": "29.99",
            },
            format="json",
        )
        assert resp.status_code == status.HTTP_201_CREATED
        assert_success(resp.data)
        assert resp.data["data"]["title"] == "Learning Django REST Framework"

    def test_student_cannot_create_course(self, auth_client, category, level):
        resp = auth_client.post(
            "/api/v1/courses/instructor/courses/",
            {
                "title": "Student Tries to Create Course",
                "description": "desc",
                "category_id": str(category.id),
            },
            format="json",
        )
        assert resp.status_code == status.HTTP_403_FORBIDDEN

    def test_unauthenticated_cannot_create_course(self, api_client, category):
        resp = api_client.post(
            "/api/v1/courses/instructor/courses/",
            {"title": "Test", "description": "desc", "category_id": str(category.id)},
            format="json",
        )
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED

    def test_instructor_can_list_own_courses(self, instructor_client, draft_course):
        resp = instructor_client.get("/api/v1/courses/instructor/courses/")
        assert resp.status_code == status.HTTP_200_OK
        assert_success(resp.data)

    def test_instructor_can_update_own_course(self, instructor_client, draft_course):
        resp = instructor_client.patch(
            f"/api/v1/courses/instructor/courses/{draft_course.id}/",
            {"title": "Updated Course Title Here"},
            format="json",
        )
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data["data"]["title"] == "Updated Course Title Here"

    def test_instructor_cannot_update_other_course(self, api_client, access_token_for_user, draft_course):
        other_instructor = InstructorFactory()
        api_client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {access_token_for_user(other_instructor)}"
        )
        resp = api_client.patch(
            f"/api/v1/courses/instructor/courses/{draft_course.id}/",
            {"title": "Someone Else Updated Title"},
            format="json",
        )
        assert resp.status_code == status.HTTP_404_NOT_FOUND

    def test_publish_course_success(self, instructor_client, draft_course):
        resp = instructor_client.post(
            f"/api/v1/courses/instructor/courses/{draft_course.id}/publish/"
        )
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data["data"]["status"] == "published"

    def test_publish_course_missing_fields_fails(self, instructor_client, instructor_user):
        """Course without required fields cannot be published."""
        incomplete_course = Course.objects.create(
            title="Incomplete Course No",
            description="",
            instructor=instructor_user,
        )
        resp = instructor_client.post(
            f"/api/v1/courses/instructor/courses/{incomplete_course.id}/publish/"
        )
        assert resp.status_code == status.HTTP_400_BAD_REQUEST
        assert_error(resp.data)

    def test_archive_course(self, instructor_client, draft_course):
        resp = instructor_client.post(
            f"/api/v1/courses/instructor/courses/{draft_course.id}/archive/"
        )
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data["data"]["status"] == "archived"

    def test_cannot_delete_published_course(self, instructor_client, instructor_user, category, level):
        published = Course.objects.create(
            title="Published Cannot Delete This",
            description="desc",
            instructor=instructor_user,
            category=category,
            level=level,
            featured_image="https://example.com/img.jpg",
            status=Course.Status.PUBLISHED,
        )
        resp = instructor_client.delete(
            f"/api/v1/courses/instructor/courses/{published.id}/"
        )
        assert resp.status_code == status.HTTP_400_BAD_REQUEST

    def test_title_validation_minimum_length(self, instructor_client, category):
        resp = instructor_client.post(
            "/api/v1/courses/instructor/courses/",
            {
                "title": "Short",
                "description": "desc",
                "category_id": str(category.id),
                "price": "0",
            },
            format="json",
        )
        assert resp.status_code == status.HTTP_400_BAD_REQUEST

    def test_price_cannot_be_negative(self, instructor_client, category):
        resp = instructor_client.post(
            "/api/v1/courses/instructor/courses/",
            {
                "title": "Valid Long Course Title",
                "description": "desc",
                "category_id": str(category.id),
                "price": "-10",
            },
            format="json",
        )
        assert resp.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestAdminCourseViewSet:
    def test_admin_can_list_all_courses(self, admin_client, published_course, draft_course):
        resp = admin_client.get("/api/v1/courses/admin/courses/")
        assert resp.status_code == status.HTTP_200_OK
        assert_success(resp.data)

    def test_instructor_cannot_access_admin_courses(self, instructor_client):
        resp = instructor_client.get("/api/v1/courses/admin/courses/")
        assert resp.status_code == status.HTTP_403_FORBIDDEN

    def test_admin_can_publish_any_course(self, admin_client, draft_course):
        resp = admin_client.post(
            f"/api/v1/courses/admin/courses/{draft_course.id}/publish/"
        )
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data["data"]["status"] == "published"

    def test_admin_can_delete_any_course(self, admin_client, draft_course):
        resp = admin_client.delete(
            f"/api/v1/courses/admin/courses/{draft_course.id}/"
        )
        assert resp.status_code == status.HTTP_204_NO_CONTENT
        assert not Course.objects.filter(pk=draft_course.pk).exists()

    def test_admin_can_archive_any_course(self, admin_client, draft_course):
        resp = admin_client.post(
            f"/api/v1/courses/admin/courses/{draft_course.id}/archive/"
        )
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data["data"]["status"] == "archived"

    def test_admin_can_filter_courses_by_status(self, admin_client, published_course, draft_course):
        resp = admin_client.get("/api/v1/courses/admin/courses/?status=published")
        assert resp.status_code == status.HTTP_200_OK
        results = resp.data["data"]["results"]
        assert all(c["status"] == "published" for c in results)
