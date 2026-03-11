import pytest

from apps.courses.models import Category, Course, Level
from apps.courses.services.course_service import CoursePublishError, CourseService
from tests.factories import AdminFactory, InstructorFactory


@pytest.mark.django_db
class TestCourseService:
    def setup_method(self):
        self.instructor = InstructorFactory()
        self.admin = AdminFactory()
        self.category = Category.objects.create(name="Django")
        self.level = Level.objects.create(name="Intermediate")

    def _make_course(self, **kwargs):
        defaults = {
            "title": "A Valid Course Title Here",
            "description": "Full description",
            "instructor": self.instructor,
            "category": self.category,
            "level": self.level,
            "featured_image": "https://example.com/img.jpg",
        }
        defaults.update(kwargs)
        return Course.objects.create(**defaults)

    def test_create_course_sets_instructor(self):
        course = CourseService.create_course(
            self.instructor,
            {
                "title": "Creating a Django REST API",
                "description": "desc",
                "category": self.category,
            },
        )
        assert course.instructor == self.instructor
        assert course.status == Course.Status.DRAFT

    def test_update_course_changes_fields(self):
        course = self._make_course()
        updated = CourseService.update_course(course, {"title": "Updated Course Title Here"})
        assert updated.title == "Updated Course Title Here"

    def test_publish_course_sets_status_and_published_at(self):
        course = self._make_course()
        published = CourseService.publish_course(course, self.instructor)
        assert published.status == Course.Status.PUBLISHED
        assert published.published_at is not None

    def test_publish_course_fails_without_required_fields(self):
        course = Course.objects.create(
            title="Short",
            description="",
            instructor=self.instructor,
        )
        with pytest.raises(CoursePublishError):
            CourseService.publish_course(course, self.instructor)

    def test_publish_course_fails_for_wrong_instructor(self):
        other_instructor = InstructorFactory()
        course = self._make_course()
        with pytest.raises(PermissionError):
            CourseService.publish_course(course, other_instructor)

    def test_admin_can_publish_any_course(self):
        course = self._make_course()
        published = CourseService.publish_course(course, self.admin)
        assert published.status == Course.Status.PUBLISHED

    def test_publish_archived_course_raises_error(self):
        course = self._make_course(status=Course.Status.ARCHIVED)
        with pytest.raises(CoursePublishError):
            CourseService.publish_course(course, self.instructor)

    def test_archive_course_sets_status(self):
        course = self._make_course(status=Course.Status.PUBLISHED)
        archived = CourseService.archive_course(course, self.instructor)
        assert archived.status == Course.Status.ARCHIVED

    def test_archive_course_fails_for_wrong_instructor(self):
        other_instructor = InstructorFactory()
        course = self._make_course()
        with pytest.raises(PermissionError):
            CourseService.archive_course(course, other_instructor)

    def test_get_course_by_slug_returns_published_course(self):
        course = self._make_course(status=Course.Status.PUBLISHED)
        found = CourseService.get_course_by_slug(course.slug)
        assert found.pk == course.pk

    def test_get_course_by_slug_raises_for_draft(self):
        course = self._make_course(status=Course.Status.DRAFT)
        with pytest.raises(Course.DoesNotExist):
            CourseService.get_course_by_slug(course.slug)

    def test_list_public_courses_returns_only_published(self):
        self._make_course(status=Course.Status.PUBLISHED)
        self._make_course(title="Draft Course Not Shown", status=Course.Status.DRAFT)
        courses = CourseService.list_public_courses()
        assert all(c.status == Course.Status.PUBLISHED for c in courses)

    def test_get_instructor_courses_returns_own_courses(self):
        other_instructor = InstructorFactory()
        course1 = self._make_course()
        Course.objects.create(
            title="Other Instructor Course",
            description="desc",
            instructor=other_instructor,
        )
        courses = CourseService.get_instructor_courses(self.instructor)
        pks = list(courses.values_list("pk", flat=True))
        assert course1.pk in pks
        assert len(pks) == 1

    def test_generate_unique_slug_avoids_duplicates(self):
        Course.objects.create(
            title="Python Basics Here",
            description="desc",
            instructor=self.instructor,
            slug="python-basics-here",
        )
        slug = CourseService.generate_unique_slug("Python Basics Here")
        assert slug == "python-basics-here-1"
