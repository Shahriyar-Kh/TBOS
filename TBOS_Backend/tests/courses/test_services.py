"""Tests for courses service layer."""
import pytest
from rest_framework.exceptions import PermissionDenied, ValidationError

from apps.courses.models import Category, Course, Language, Level
from apps.courses.services.course_service import CourseService


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
def draft_course(db, instructor_user, category, level):
    return Course.objects.create(
        title="Django REST Framework",
        description="Master Django REST Framework",
        instructor=instructor_user,
        category=category,
        level=level,
        thumbnail="https://example.com/thumb.jpg",
        price="59.99",
    )


class TestCreateCourse:
    def test_creates_course_with_instructor(self, db, instructor_user, category):
        data = {
            "title": "New Python Course",
            "description": "Learn Python",
            "category_id": category.id,
            "price": "29.99",
        }
        course = CourseService.create_course(instructor=instructor_user, validated_data=data)
        assert course.instructor == instructor_user
        assert course.status == Course.Status.DRAFT
        assert course.slug == "new-python-course"

    def test_creates_course_with_unique_slug(self, db, instructor_user, category):
        CourseService.create_course(
            instructor=instructor_user,
            validated_data={"title": "Duplicate", "description": "d", "category_id": category.id, "price": "0"},
        )
        course2 = CourseService.create_course(
            instructor=instructor_user,
            validated_data={"title": "Duplicate", "description": "d2", "category_id": category.id, "price": "0"},
        )
        assert course2.slug == "duplicate-1"


class TestUpdateCourse:
    def test_updates_course_fields(self, draft_course):
        updated = CourseService.update_course(
            course=draft_course,
            validated_data={"subtitle": "Advanced guide", "price": "79.99"},
        )
        assert updated.subtitle == "Advanced guide"
        assert float(updated.price) == 79.99

    def test_slug_regenerated_on_title_change(self, draft_course):
        updated = CourseService.update_course(
            course=draft_course,
            validated_data={"title": "Updated Title For Course"},
        )
        assert updated.slug == "updated-title-for-course"


class TestPublishCourse:
    def test_instructor_can_publish_own_course(self, draft_course, instructor_user):
        published = CourseService.publish_course(
            course=draft_course, user=instructor_user
        )
        assert published.status == Course.Status.PUBLISHED
        assert published.published_at is not None

    def test_instructor_cannot_publish_others_course(self, draft_course, db):
        from tests.factories import InstructorFactory
        other_instructor = InstructorFactory()
        with pytest.raises(PermissionDenied):
            CourseService.publish_course(course=draft_course, user=other_instructor)

    def test_admin_can_publish_any_course(self, draft_course, admin_user):
        published = CourseService.publish_course(
            course=draft_course, user=admin_user
        )
        assert published.status == Course.Status.PUBLISHED

    def test_publish_fails_without_required_fields(self, db, instructor_user, category):
        course = Course.objects.create(
            title="Incomplete Course",
            description="Missing thumbnail and level",
            instructor=instructor_user,
            category=category,
            price="0",
        )
        with pytest.raises(ValidationError):
            CourseService.publish_course(course=course, user=instructor_user)

    def test_archived_course_cannot_be_published(self, draft_course, instructor_user):
        draft_course.status = Course.Status.ARCHIVED
        draft_course.save()
        with pytest.raises(ValidationError):
            CourseService.publish_course(course=draft_course, user=instructor_user)


class TestArchiveCourse:
    def test_instructor_can_archive_own_course(self, draft_course, instructor_user):
        archived = CourseService.archive_course(
            course=draft_course, user=instructor_user
        )
        assert archived.status == Course.Status.ARCHIVED

    def test_instructor_cannot_archive_others_course(self, draft_course, db):
        from tests.factories import InstructorFactory
        other_instructor = InstructorFactory()
        with pytest.raises(PermissionDenied):
            CourseService.archive_course(course=draft_course, user=other_instructor)

    def test_already_archived_raises_error(self, draft_course, instructor_user):
        draft_course.status = Course.Status.ARCHIVED
        draft_course.save()
        with pytest.raises(ValidationError):
            CourseService.archive_course(course=draft_course, user=instructor_user)


class TestGetCourseBySlug:
    def test_returns_published_course(self, draft_course, instructor_user):
        draft_course.thumbnail = "https://example.com/thumb.jpg"
        draft_course.status = Course.Status.PUBLISHED
        draft_course.save()
        found = CourseService.get_course_by_slug(draft_course.slug)
        assert found.pk == draft_course.pk

    def test_raises_for_draft_course(self, draft_course):
        with pytest.raises(Course.DoesNotExist):
            CourseService.get_course_by_slug(draft_course.slug)


class TestListPublicCourses:
    def test_returns_only_published_courses(self, db, instructor_user, category, level):
        Course.objects.create(
            title="Published",
            description="p",
            instructor=instructor_user,
            category=category,
            level=level,
            thumbnail="https://example.com/t.jpg",
            status=Course.Status.PUBLISHED,
            price="0",
        )
        Course.objects.create(
            title="Draft",
            description="d",
            instructor=instructor_user,
            category=category,
            price="0",
        )
        qs = CourseService.list_public_courses()
        titles = list(qs.values_list("title", flat=True))
        assert "Published" in titles
        assert "Draft" not in titles

    def test_filters_by_category_slug(self, db, instructor_user):
        cat1 = Category.objects.create(name="Cat1")
        cat2 = Category.objects.create(name="Cat2")
        level = Level.objects.create(name="Any")
        Course.objects.create(
            title="Cat1 Course",
            description="x",
            instructor=instructor_user,
            category=cat1,
            level=level,
            thumbnail="https://example.com/t.jpg",
            status=Course.Status.PUBLISHED,
            price="0",
        )
        Course.objects.create(
            title="Cat2 Course",
            description="y",
            instructor=instructor_user,
            category=cat2,
            level=level,
            thumbnail="https://example.com/t.jpg",
            status=Course.Status.PUBLISHED,
            price="0",
        )
        qs = CourseService.list_public_courses({"category": "cat1"})
        assert qs.count() == 1
        assert qs.first().title == "Cat1 Course"


class TestGetInstructorCourses:
    def test_returns_own_courses_only(self, db, instructor_user, category):
        from tests.factories import InstructorFactory
        other_instructor = InstructorFactory()
        c1 = Course.objects.create(
            title="My Course", description="x", instructor=instructor_user,
            category=category, price="0"
        )
        Course.objects.create(
            title="Other Course", description="y", instructor=other_instructor,
            category=category, price="0"
        )
        qs = CourseService.get_instructor_courses(instructor_user)
        assert qs.count() == 1
        assert qs.first() == c1


class TestGenerateUniqueSlug:
    def test_generates_base_slug(self, db):
        slug = CourseService.generate_unique_slug("Python Tutorial")
        assert slug == "python-tutorial"

    def test_appends_counter_on_conflict(self, db, instructor_user, category):
        Course.objects.create(
            title="Conflict Course", description="x",
            instructor=instructor_user, category=category, price="0"
        )
        slug = CourseService.generate_unique_slug("Conflict Course")
        assert slug == "conflict-course-1"
