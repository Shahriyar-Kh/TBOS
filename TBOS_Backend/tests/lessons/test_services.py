"""Tests for lesson service layer."""
import pytest

from apps.lessons.models import CourseSection, Lesson
from apps.lessons.services.lesson_service import LessonService
from tests.factories import CourseSectionFactory, CourseFactory, LessonFactory


class TestLessonServiceSections:
    def test_create_section(self, db):
        course = CourseFactory()
        data = {"title": "Introduction", "description": "Intro section", "order": 1}
        section = LessonService.create_section(course=course, validated_data=data)
        assert section.course == course
        assert section.title == "Introduction"
        assert section.order == 1

    def test_update_section(self, db):
        section = CourseSectionFactory(title="Old Title", order=1)
        updated = LessonService.update_section(
            section=section, validated_data={"title": "New Title", "order": 2}
        )
        assert updated.title == "New Title"
        assert updated.order == 2

    def test_delete_section(self, db):
        section = CourseSectionFactory()
        section_id = section.id
        LessonService.delete_section(section)
        assert not CourseSection.objects.filter(id=section_id).exists()

    def test_delete_section_cascades_lessons(self, db):
        section = CourseSectionFactory()
        lesson = LessonFactory(section=section)
        lesson_id = lesson.id
        LessonService.delete_section(section)
        assert not Lesson.objects.filter(id=lesson_id).exists()

    def test_reorder_sections(self, db):
        course = CourseFactory()
        s1 = CourseSectionFactory(course=course, order=1)
        s2 = CourseSectionFactory(course=course, order=2)
        s3 = CourseSectionFactory(course=course, order=3)
        # Swap s1 and s3
        LessonService.reorder_sections(
            course_id=course.id,
            section_order=[
                {"id": s1.id, "order": 3},
                {"id": s3.id, "order": 1},
            ],
        )
        s1.refresh_from_db()
        s3.refresh_from_db()
        assert s1.order == 3
        assert s3.order == 1


class TestLessonServiceLessons:
    def test_create_lesson(self, db):
        section = CourseSectionFactory()
        data = {
            "title": "First Lesson",
            "description": "Learn stuff",
            "lesson_type": Lesson.LessonType.VIDEO,
            "order": 1,
            "is_preview": True,
            "duration_seconds": 600,
        }
        lesson = LessonService.create_lesson(section=section, validated_data=data)
        assert lesson.section == section
        assert lesson.title == "First Lesson"
        assert lesson.is_preview is True

    def test_update_lesson(self, db):
        lesson = LessonFactory(title="Old Title", order=1)
        updated = LessonService.update_lesson(
            lesson=lesson,
            validated_data={"title": "New Title", "order": 2, "is_preview": True},
        )
        assert updated.title == "New Title"
        assert updated.order == 2
        assert updated.is_preview is True

    def test_delete_lesson(self, db):
        lesson = LessonFactory()
        lesson_id = lesson.id
        LessonService.delete_lesson(lesson)
        assert not Lesson.objects.filter(id=lesson_id).exists()

    def test_reorder_lessons(self, db):
        section = CourseSectionFactory()
        l1 = LessonFactory(section=section, order=1)
        l2 = LessonFactory(section=section, order=2)
        l3 = LessonFactory(section=section, order=3)
        LessonService.reorder_lessons(
            section_id=section.id,
            lesson_order=[
                {"id": l1.id, "order": 3},
                {"id": l3.id, "order": 1},
            ],
        )
        l1.refresh_from_db()
        l3.refresh_from_db()
        assert l1.order == 3
        assert l3.order == 1

    def test_get_course_curriculum(self, db):
        course = CourseFactory()
        section = CourseSectionFactory(course=course, order=1)
        LessonFactory(section=section, order=1)
        LessonFactory(section=section, order=2)

        result = LessonService.get_course_curriculum(slug=course.slug)
        assert result.id == course.id
        assert result.sections.count() == 1

    def test_get_course_curriculum_not_found(self, db):
        from apps.courses.models import Course
        with pytest.raises(Course.DoesNotExist):
            LessonService.get_course_curriculum(slug="nonexistent-slug")
