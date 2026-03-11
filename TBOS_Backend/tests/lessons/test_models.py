"""Tests for lesson and section models."""
import pytest

from apps.lessons.models import CourseSection, Lesson
from tests.factories import CourseSectionFactory, CourseFactory, LessonFactory


class TestCourseSectionModel:
    def test_section_str(self, db):
        course = CourseFactory(title="Python Course")
        section = CourseSectionFactory(course=course, title="Introduction", order=1)
        assert "Introduction" in str(section)
        assert "Python Course" in str(section)

    def test_section_ordering(self, db):
        course = CourseFactory()
        s3 = CourseSectionFactory(course=course, order=3)
        s1 = CourseSectionFactory(course=course, order=1)
        s2 = CourseSectionFactory(course=course, order=2)
        sections = list(CourseSection.objects.filter(course=course))
        assert sections[0] == s1
        assert sections[1] == s2
        assert sections[2] == s3

    def test_section_belongs_to_course(self, db):
        course = CourseFactory()
        section = CourseSectionFactory(course=course)
        assert section.course == course

    def test_section_cascade_delete(self, db):
        course = CourseFactory()
        section = CourseSectionFactory(course=course)
        lesson = LessonFactory(section=section)
        course.delete()
        assert not CourseSection.objects.filter(id=section.id).exists()
        assert not Lesson.objects.filter(id=lesson.id).exists()


class TestLessonModel:
    def test_lesson_str(self, db):
        section = CourseSectionFactory(title="Introduction")
        lesson = LessonFactory(section=section, title="Course Overview", order=1)
        assert "Course Overview" in str(lesson)
        assert "Introduction" in str(lesson)

    def test_lesson_ordering(self, db):
        section = CourseSectionFactory()
        l3 = LessonFactory(section=section, order=3)
        l1 = LessonFactory(section=section, order=1)
        l2 = LessonFactory(section=section, order=2)
        lessons = list(Lesson.objects.filter(section=section))
        assert lessons[0] == l1
        assert lessons[1] == l2
        assert lessons[2] == l3

    def test_lesson_types(self, db):
        section = CourseSectionFactory()
        for lt in [
            Lesson.LessonType.VIDEO,
            Lesson.LessonType.QUIZ,
            Lesson.LessonType.ASSIGNMENT,
            Lesson.LessonType.ARTICLE,
        ]:
            lesson = LessonFactory(section=section, lesson_type=lt)
            assert lesson.lesson_type == lt

    def test_article_lesson_content(self, db):
        section = CourseSectionFactory()
        lesson = LessonFactory(
            section=section,
            lesson_type=Lesson.LessonType.ARTICLE,
            article_content="Long text content here.",
        )
        assert lesson.article_content == "Long text content here."

    def test_preview_flag(self, db):
        section = CourseSectionFactory()
        preview = LessonFactory(section=section, is_preview=True)
        non_preview = LessonFactory(section=section, is_preview=False)
        assert preview.is_preview is True
        assert non_preview.is_preview is False

    def test_lesson_cascade_delete_with_section(self, db):
        section = CourseSectionFactory()
        lesson = LessonFactory(section=section)
        section.delete()
        assert not Lesson.objects.filter(id=lesson.id).exists()
