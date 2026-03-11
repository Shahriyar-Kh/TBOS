"""Tests for lessons and sections API views."""
import pytest
from rest_framework import status

from apps.courses.models import Course
from apps.lessons.models import CourseSection, Lesson
from tests.factories import (
    CourseSectionFactory,
    CourseFactory,
    LessonFactory,
    InstructorFactory,
)


# ──────────────────────────────────────────────────────────────
# Fixtures
# ──────────────────────────────────────────────────────────────

@pytest.fixture
def course(db, instructor_user):
    return CourseFactory(instructor=instructor_user)


@pytest.fixture
def other_instructor(db):
    return InstructorFactory()


@pytest.fixture
def other_course(db, other_instructor):
    return CourseFactory(instructor=other_instructor)


@pytest.fixture
def section(db, course):
    return CourseSectionFactory(course=course, order=1)


@pytest.fixture
def lesson(db, section):
    return LessonFactory(section=section, order=1)


# ──────────────────────────────────────────────────────────────
# Curriculum endpoint
# ──────────────────────────────────────────────────────────────

class TestCourseCurriculumView:
    def test_curriculum_returns_sections_and_lessons(
        self, api_client, course, section, lesson
    ):
        url = f"/api/v1/courses/{course.slug}/curriculum/"
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        data = response.data["data"]
        assert data["slug"] == course.slug
        assert len(data["sections"]) == 1
        assert len(data["sections"][0]["lessons"]) == 1

    def test_curriculum_not_found(self, api_client, db):
        response = api_client.get("/api/v1/courses/nonexistent/curriculum/")
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_curriculum_accessible_without_auth(self, api_client, course, section):
        url = f"/api/v1/courses/{course.slug}/curriculum/"
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK

    def test_curriculum_sections_ordered(self, api_client, db, instructor_user):
        course = CourseFactory(instructor=instructor_user)
        CourseSectionFactory(course=course, title="Section B", order=2)
        CourseSectionFactory(course=course, title="Section A", order=1)
        url = f"/api/v1/courses/{course.slug}/curriculum/"
        response = api_client.get(url)
        sections = response.data["data"]["sections"]
        assert sections[0]["title"] == "Section A"
        assert sections[1]["title"] == "Section B"


# ──────────────────────────────────────────────────────────────
# Instructor section management
# ──────────────────────────────────────────────────────────────

class TestInstructorSectionViewSet:
    def test_create_section(self, instructor_client, course):
        payload = {"course": str(course.id), "title": "Introduction", "description": "Intro", "order": 1}
        response = instructor_client.post("/api/v1/lessons/instructor/sections/", payload)
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["data"]["title"] == "Introduction"

    def test_create_section_requires_auth(self, api_client, course):
        payload = {"course": str(course.id), "title": "Intro", "order": 1}
        response = api_client.post("/api/v1/lessons/instructor/sections/", payload)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_student_cannot_create_section(self, auth_client, course):
        payload = {"course": str(course.id), "title": "Intro", "order": 1}
        response = auth_client.post("/api/v1/lessons/instructor/sections/", payload)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_instructor_cannot_create_section_for_other_course(
        self, instructor_client, other_course
    ):
        payload = {"course": str(other_course.id), "title": "Intro", "order": 1}
        response = instructor_client.post("/api/v1/lessons/instructor/sections/", payload)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_update_section(self, instructor_client, section):
        payload = {"title": "Updated Title", "order": 2}
        response = instructor_client.put(
            f"/api/v1/lessons/instructor/sections/{section.id}/", payload
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data["data"]["title"] == "Updated Title"

    def test_partial_update_section(self, instructor_client, section):
        response = instructor_client.patch(
            f"/api/v1/lessons/instructor/sections/{section.id}/",
            {"title": "Patched Title"},
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data["data"]["title"] == "Patched Title"

    def test_delete_section(self, instructor_client, section):
        response = instructor_client.delete(
            f"/api/v1/lessons/instructor/sections/{section.id}/"
        )
        assert response.status_code == status.HTTP_200_OK
        assert not CourseSection.objects.filter(id=section.id).exists()

    def test_list_sections_filtered_by_course(self, instructor_client, course, section, db):
        # Create another course's section that should not appear
        other_section = CourseSectionFactory()
        response = instructor_client.get(
            f"/api/v1/lessons/instructor/sections/?course={course.id}"
        )
        assert response.status_code == status.HTTP_200_OK
        ids = [s["id"] for s in response.data["data"]["results"]]
        assert str(section.id) in ids
        assert str(other_section.id) not in ids

    def test_reorder_sections(self, instructor_client, db, instructor_user):
        course = CourseFactory(instructor=instructor_user)
        s1 = CourseSectionFactory(course=course, order=1)
        s2 = CourseSectionFactory(course=course, order=2)
        payload = {
            "course_id": str(course.id),
            "order": [
                {"id": str(s1.id), "order": 2},
                {"id": str(s2.id), "order": 1},
            ],
        }
        response = instructor_client.post(
            "/api/v1/lessons/instructor/sections/reorder/", payload, format="json"
        )
        assert response.status_code == status.HTTP_200_OK
        s1.refresh_from_db()
        s2.refresh_from_db()
        assert s1.order == 2
        assert s2.order == 1


# ──────────────────────────────────────────────────────────────
# Instructor lesson management
# ──────────────────────────────────────────────────────────────

class TestInstructorLessonViewSet:
    def test_create_lesson(self, instructor_client, section):
        payload = {
            "section": str(section.id),
            "title": "Course Overview",
            "lesson_type": "video",
            "order": 1,
            "is_preview": True,
            "duration_seconds": 300,
        }
        response = instructor_client.post("/api/v1/lessons/instructor/lessons/", payload)
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["data"]["title"] == "Course Overview"
        assert response.data["data"]["is_preview"] is True

    def test_create_lesson_requires_auth(self, api_client, section):
        payload = {"section": str(section.id), "title": "Test", "lesson_type": "video", "order": 1}
        response = api_client.post("/api/v1/lessons/instructor/lessons/", payload)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_student_cannot_create_lesson(self, auth_client, section):
        payload = {"section": str(section.id), "title": "Test", "lesson_type": "video", "order": 1}
        response = auth_client.post("/api/v1/lessons/instructor/lessons/", payload)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_update_lesson(self, instructor_client, lesson):
        payload = {
            "title": "Updated Lesson",
            "lesson_type": "article",
            "order": 2,
            "is_preview": True,
            "duration_seconds": 0,
            "article_content": "Some content",
        }
        response = instructor_client.put(
            f"/api/v1/lessons/instructor/lessons/{lesson.id}/", payload
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data["data"]["title"] == "Updated Lesson"
        assert response.data["data"]["lesson_type"] == "article"

    def test_delete_lesson(self, instructor_client, lesson):
        response = instructor_client.delete(
            f"/api/v1/lessons/instructor/lessons/{lesson.id}/"
        )
        assert response.status_code == status.HTTP_200_OK
        assert not Lesson.objects.filter(id=lesson.id).exists()

    def test_list_lessons_filtered_by_section(self, instructor_client, lesson, section):
        response = instructor_client.get(
            f"/api/v1/lessons/instructor/lessons/?section={section.id}"
        )
        assert response.status_code == status.HTTP_200_OK
        ids = [l["id"] for l in response.data["data"]["results"]]
        assert str(lesson.id) in ids

    def test_create_article_lesson_with_content(self, instructor_client, section):
        payload = {
            "section": str(section.id),
            "title": "Python Basics Article",
            "lesson_type": "article",
            "order": 1,
            "is_preview": False,
            "duration_seconds": 0,
            "article_content": "# Python Basics\n\nWelcome to Python!",
        }
        response = instructor_client.post("/api/v1/lessons/instructor/lessons/", payload)
        assert response.status_code == status.HTTP_201_CREATED
        assert "Python Basics" in response.data["data"]["article_content"]

    def test_reorder_lessons(self, instructor_client, section):
        l1 = LessonFactory(section=section, order=1)
        l2 = LessonFactory(section=section, order=2)
        payload = {
            "section_id": str(section.id),
            "order": [
                {"id": str(l1.id), "order": 2},
                {"id": str(l2.id), "order": 1},
            ],
        }
        response = instructor_client.post(
            "/api/v1/lessons/instructor/lessons/reorder/", payload, format="json"
        )
        assert response.status_code == status.HTTP_200_OK
        l1.refresh_from_db()
        l2.refresh_from_db()
        assert l1.order == 2
        assert l2.order == 1


# ──────────────────────────────────────────────────────────────
# Validation tests
# ──────────────────────────────────────────────────────────────

class TestLessonValidation:
    def test_short_title_rejected(self, instructor_client, section):
        payload = {
            "section": str(section.id),
            "title": "ab",
            "lesson_type": "video",
            "order": 1,
        }
        response = instructor_client.post("/api/v1/lessons/instructor/lessons/", payload)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_section_title_required(self, instructor_client, course):
        payload = {"course": str(course.id), "order": 1}
        response = instructor_client.post("/api/v1/lessons/instructor/sections/", payload)
        assert response.status_code == status.HTTP_400_BAD_REQUEST


# ──────────────────────────────────────────────────────────────
# Admin tests
# ──────────────────────────────────────────────────────────────

class TestAdminCanManageCurriculum:
    def test_admin_can_list_all_sections(self, admin_client, section):
        response = admin_client.get("/api/v1/lessons/instructor/sections/")
        assert response.status_code == status.HTTP_200_OK

    def test_admin_can_create_section(self, admin_client, course):
        payload = {"course": str(course.id), "title": "Admin Section", "order": 1}
        response = admin_client.post("/api/v1/lessons/instructor/sections/", payload)
        assert response.status_code == status.HTTP_201_CREATED
