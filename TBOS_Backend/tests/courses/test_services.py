import pytest

from apps.courses.models import Course
from apps.courses.services.course_service import CourseService
from tests.factories import (
    CategoryFactory,
    CourseFactory,
    InstructorFactory,
    LanguageFactory,
    LevelFactory,
)


@pytest.mark.django_db
class TestCourseServiceCreateCourse:
    def test_create_course_returns_course_instance(self):
        instructor = InstructorFactory()
        category = CategoryFactory(name="Service Cat 1")

        course = CourseService.create_course(
            instructor,
            {
                "title": "Service Course",
                "description": "Test description",
                "category": category,
            },
        )

        assert isinstance(course, Course)
        assert course.pk is not None

    def test_create_course_assigns_instructor(self):
        instructor = InstructorFactory()
        category = CategoryFactory(name="Service Cat 2")

        course = CourseService.create_course(
            instructor,
            {
                "title": "Instructor Course",
                "description": "Test description",
                "category": category,
            },
        )

        assert course.instructor == instructor

    def test_create_course_persists_to_database(self):
        instructor = InstructorFactory()
        category = CategoryFactory(name="Service Cat 3")

        course = CourseService.create_course(
            instructor,
            {
                "title": "Persisted Course",
                "description": "desc",
                "category": category,
            },
        )

        from_db = Course.objects.get(pk=course.pk)
        assert from_db.title == "Persisted Course"

    def test_create_course_sets_default_draft_status(self):
        instructor = InstructorFactory()
        category = CategoryFactory(name="Service Cat 4")

        course = CourseService.create_course(
            instructor,
            {
                "title": "Draft Service Course",
                "description": "desc",
                "category": category,
            },
        )

        assert course.status == Course.Status.DRAFT

    def test_create_course_with_all_optional_fields(self):
        instructor = InstructorFactory()
        category = CategoryFactory(name="Service Cat 5")
        level = LevelFactory(name="Beginner Svc")
        language = LanguageFactory(name="English Svc")

        course = CourseService.create_course(
            instructor,
            {
                "title": "Full Course",
                "description": "desc",
                "category": category,
                "level": level,
                "language": language,
                "price": 99.99,
                "is_free": False,
            },
        )

        assert course.level == level
        assert course.language == language
        assert float(course.price) == pytest.approx(99.99)


@pytest.mark.django_db
class TestCourseServiceGenerateUniqueSlug:
    def test_generates_slug_from_title(self):
        slug = CourseService.generate_unique_slug("Django for Beginners")

        assert slug == "django-for-beginners"

    def test_generated_slug_is_unique_when_conflict(self):
        CourseFactory(title="Conflict Title")

        slug = CourseService.generate_unique_slug("Conflict Title")

        assert slug == "conflict-title-1"

    def test_generated_slug_increments_counter(self):
        CourseFactory(title="Multi Conflict")
        CourseFactory(title="Multi Conflict")

        slug = CourseService.generate_unique_slug("Multi Conflict")

        assert slug == "multi-conflict-2"

    def test_exclude_pk_allows_same_slug_for_self(self):
        course = CourseFactory(title="Unique Slug Course")

        slug = CourseService.generate_unique_slug("Unique Slug Course", exclude_pk=course.pk)

        assert slug == "unique-slug-course"

    def test_slug_handles_special_characters(self):
        slug = CourseService.generate_unique_slug("Python & Django: REST APIs!")

        assert slug == "python-django-rest-apis"

    def test_slug_converts_spaces_to_hyphens(self):
        slug = CourseService.generate_unique_slug("Hello World Course")

        assert slug == "hello-world-course"


@pytest.mark.django_db
class TestCourseServiceUpdateAggregateStats:
    def test_update_stats_sets_total_lessons(self):
        course = CourseFactory()

        CourseService.update_aggregate_stats(course)
        course.refresh_from_db()

        assert course.total_lessons == 0

    def test_update_stats_sets_total_enrollments(self):
        course = CourseFactory()

        CourseService.update_aggregate_stats(course)
        course.refresh_from_db()

        assert course.total_enrollments == 0

    def test_update_stats_sets_average_rating_to_zero_with_no_reviews(self):
        course = CourseFactory()

        CourseService.update_aggregate_stats(course)
        course.refresh_from_db()

        assert float(course.average_rating) == 0.0

    def test_update_stats_persists_to_database(self):
        course = CourseFactory()
        course.total_lessons = 99
        course.save(update_fields=["total_lessons"])

        CourseService.update_aggregate_stats(course)
        course.refresh_from_db()

        assert course.total_lessons == 0
