"""Tests for lesson and section serializers."""
import pytest
from rest_framework.exceptions import ValidationError

from apps.lessons.models import Lesson
from apps.lessons.serializers import (
    CourseSectionCreateSerializer,
    CourseSectionUpdateSerializer,
    LessonCreateSerializer,
    LessonUpdateSerializer,
)
from tests.factories import CourseSectionFactory, CourseFactory


class TestCourseSectionCreateSerializer:
    def test_valid_data(self, db):
        course = CourseFactory()
        data = {"course": course.id, "title": "Introduction", "order": 1}
        serializer = CourseSectionCreateSerializer(data=data)
        assert serializer.is_valid(), serializer.errors

    def test_title_required(self, db):
        course = CourseFactory()
        data = {"course": course.id, "order": 1}
        serializer = CourseSectionCreateSerializer(data=data)
        assert not serializer.is_valid()
        assert "title" in serializer.errors

    def test_negative_order_rejected(self, db):
        course = CourseFactory()
        data = {"course": course.id, "title": "Intro", "order": -1}
        serializer = CourseSectionCreateSerializer(data=data)
        assert not serializer.is_valid()
        assert "order" in serializer.errors


class TestCourseSectionUpdateSerializer:
    def test_valid_update(self, db):
        section = CourseSectionFactory()
        data = {"title": "New Title", "order": 2}
        serializer = CourseSectionUpdateSerializer(instance=section, data=data)
        assert serializer.is_valid(), serializer.errors

    def test_negative_order_rejected(self, db):
        section = CourseSectionFactory()
        data = {"title": "Title", "order": -5}
        serializer = CourseSectionUpdateSerializer(instance=section, data=data)
        assert not serializer.is_valid()
        assert "order" in serializer.errors


class TestLessonCreateSerializer:
    def test_valid_data(self, db):
        section = CourseSectionFactory()
        data = {
            "section": section.id,
            "title": "First Lesson",
            "lesson_type": "video",
            "order": 1,
        }
        serializer = LessonCreateSerializer(data=data)
        assert serializer.is_valid(), serializer.errors

    def test_short_title_rejected(self, db):
        section = CourseSectionFactory()
        data = {
            "section": section.id,
            "title": "ab",
            "lesson_type": "video",
            "order": 1,
        }
        serializer = LessonCreateSerializer(data=data)
        assert not serializer.is_valid()
        assert "title" in serializer.errors

    def test_invalid_lesson_type_rejected(self, db):
        section = CourseSectionFactory()
        data = {
            "section": section.id,
            "title": "Valid Title",
            "lesson_type": "invalid_type",
            "order": 1,
        }
        serializer = LessonCreateSerializer(data=data)
        assert not serializer.is_valid()
        assert "lesson_type" in serializer.errors

    def test_all_lesson_types_valid(self, db):
        section = CourseSectionFactory()
        for lt in ["video", "quiz", "assignment", "article"]:
            data = {
                "section": section.id,
                "title": "Valid Title",
                "lesson_type": lt,
                "order": 1,
            }
            serializer = LessonCreateSerializer(data=data)
            assert serializer.is_valid(), f"Failed for type: {lt} - {serializer.errors}"


class TestLessonUpdateSerializer:
    def test_valid_update(self, db):
        data = {
            "title": "Updated Lesson",
            "lesson_type": "article",
            "order": 2,
        }
        serializer = LessonUpdateSerializer(data=data)
        assert serializer.is_valid(), serializer.errors

    def test_short_title_rejected(self, db):
        data = {"title": "ab", "lesson_type": "video", "order": 1}
        serializer = LessonUpdateSerializer(data=data)
        assert not serializer.is_valid()
        assert "title" in serializer.errors
