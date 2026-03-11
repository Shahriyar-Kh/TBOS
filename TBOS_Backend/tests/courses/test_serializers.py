import pytest
from rest_framework.test import APIRequestFactory

from apps.courses.models import Course
from apps.courses.serializers import (
    CategorySerializer,
    CourseCreateUpdateSerializer,
    CourseDetailSerializer,
    CourseListSerializer,
    LanguageSerializer,
    LearningOutcomeSerializer,
    LevelSerializer,
    RequirementSerializer,
)
from tests.factories import (
    CategoryFactory,
    CourseFactory,
    InstructorFactory,
    LanguageFactory,
    LearningOutcomeFactory,
    LevelFactory,
    RequirementFactory,
)


@pytest.mark.django_db
class TestCategorySerializer:
    def test_serializes_category_fields(self):
        category = CategoryFactory(name="Web Dev")

        data = CategorySerializer(category).data

        assert data["name"] == "Web Dev"
        assert "id" in data
        assert "slug" in data
        assert data["slug"] == "web-dev"

    def test_slug_is_read_only(self):
        category = CategoryFactory(name="Backend")
        serializer = CategorySerializer(
            category, data={"name": "Backend", "slug": "custom-slug"}
        )

        assert serializer.is_valid()
        assert serializer.validated_data.get("slug") is None


@pytest.mark.django_db
class TestLevelSerializer:
    def test_serializes_level_fields(self):
        level = LevelFactory(name="Beginner")

        data = LevelSerializer(level).data

        assert data["name"] == "Beginner"
        assert "id" in data

    def test_id_is_read_only(self):
        level = LevelFactory(name="Intermediate")
        serializer = LevelSerializer(level, data={"name": "Advanced"})

        assert serializer.is_valid()
        assert "id" not in serializer.validated_data


@pytest.mark.django_db
class TestLanguageSerializer:
    def test_serializes_language_fields(self):
        language = LanguageFactory(name="English")

        data = LanguageSerializer(language).data

        assert data["name"] == "English"
        assert "id" in data


@pytest.mark.django_db
class TestLearningOutcomeSerializer:
    def test_serializes_learning_outcome_fields(self):
        outcome = LearningOutcomeFactory(text="Master Django", order=1)

        data = LearningOutcomeSerializer(outcome).data

        assert data["text"] == "Master Django"
        assert data["order"] == 1
        assert "id" in data


@pytest.mark.django_db
class TestRequirementSerializer:
    def test_serializes_requirement_fields(self):
        req = RequirementFactory(text="Know Python", order=0)

        data = RequirementSerializer(req).data

        assert data["text"] == "Know Python"
        assert data["order"] == 0
        assert "id" in data


@pytest.mark.django_db
class TestCourseListSerializer:
    def test_serializes_required_list_fields(self):
        course = CourseFactory(
            title="Test Course",
            status=Course.Status.PUBLISHED,
        )

        data = CourseListSerializer(course).data

        assert data["title"] == "Test Course"
        assert "slug" in data
        assert "category" in data
        assert "level" in data
        assert "instructor_name" in data
        assert "average_rating" in data
        assert "total_enrollments" in data
        assert "effective_price" in data
        assert "status" in data

    def test_instructor_name_populated(self):
        instructor = InstructorFactory(first_name="Jane", last_name="Doe")
        course = CourseFactory(instructor=instructor)

        data = CourseListSerializer(course).data

        assert data["instructor_name"] == "Jane Doe"

    def test_nested_category_included(self):
        category = CategoryFactory(name="Data Science")
        course = CourseFactory(category=category)

        data = CourseListSerializer(course).data

        assert data["category"]["name"] == "Data Science"
        assert data["category"]["slug"] == "data-science"


@pytest.mark.django_db
class TestCourseDetailSerializer:
    def test_serializes_detail_fields(self):
        course = CourseFactory(title="Advanced DRF")
        LearningOutcomeFactory(course=course, text="Build APIs")
        RequirementFactory(course=course, text="Know Python")

        data = CourseDetailSerializer(course).data

        assert data["title"] == "Advanced DRF"
        assert "description" in data
        assert "instructor_name" in data
        assert "instructor_id" in data
        assert "average_rating" in data
        assert "total_enrollments" in data
        assert len(data["learning_outcomes"]) == 1
        assert len(data["requirements"]) == 1
        assert data["learning_outcomes"][0]["text"] == "Build APIs"
        assert data["requirements"][0]["text"] == "Know Python"

    def test_nested_language_included(self):
        language = LanguageFactory(name="Farsi")
        course = CourseFactory(language=language)

        data = CourseDetailSerializer(course).data

        assert data["language"]["name"] == "Farsi"

    def test_instructor_id_is_uuid_string(self):
        instructor = InstructorFactory()
        course = CourseFactory(instructor=instructor)

        data = CourseDetailSerializer(course).data

        assert data["instructor_id"] == str(instructor.id)


@pytest.mark.django_db
class TestCourseCreateUpdateSerializer:
    def _make_request(self, user):
        factory = APIRequestFactory()
        request = factory.post("/")
        request.user = user
        return request

    def test_valid_creation_with_required_fields(self):
        instructor = InstructorFactory()
        category = CategoryFactory(name="Programming")
        request = self._make_request(instructor)

        data = {
            "title": "My New Course",
            "description": "Course description",
            "category_id": str(category.id),
        }
        serializer = CourseCreateUpdateSerializer(
            data=data, context={"request": request}
        )

        assert serializer.is_valid(), serializer.errors
        course = serializer.save()
        assert course.title == "My New Course"
        assert course.instructor == instructor
        assert course.category == category

    def test_missing_title_is_invalid(self):
        instructor = InstructorFactory()
        category = CategoryFactory(name="Cat for Missing Title")
        request = self._make_request(instructor)

        data = {
            "description": "Course description",
            "category_id": str(category.id),
        }
        serializer = CourseCreateUpdateSerializer(
            data=data, context={"request": request}
        )

        assert not serializer.is_valid()
        assert "title" in serializer.errors

    def test_invalid_category_id_fails(self):
        instructor = InstructorFactory()
        request = self._make_request(instructor)

        data = {
            "title": "Course",
            "description": "desc",
            "category_id": "00000000-0000-0000-0000-000000000000",
        }
        serializer = CourseCreateUpdateSerializer(
            data=data, context={"request": request}
        )

        assert not serializer.is_valid()
        assert "category_id" in serializer.errors

    def test_optional_level_id_accepted(self):
        instructor = InstructorFactory()
        category = CategoryFactory(name="Cat for Level")
        level = LevelFactory(name="Beginner Level")
        request = self._make_request(instructor)

        data = {
            "title": "Course With Level",
            "description": "desc",
            "category_id": str(category.id),
            "level_id": str(level.id),
        }
        serializer = CourseCreateUpdateSerializer(
            data=data, context={"request": request}
        )

        assert serializer.is_valid(), serializer.errors
        course = serializer.save()
        assert course.level == level

    def test_optional_language_id_accepted(self):
        instructor = InstructorFactory()
        category = CategoryFactory(name="Cat for Language")
        language = LanguageFactory(name="English Serializer Test")
        request = self._make_request(instructor)

        data = {
            "title": "Course With Language",
            "description": "desc",
            "category_id": str(category.id),
            "language_id": str(language.id),
        }
        serializer = CourseCreateUpdateSerializer(
            data=data, context={"request": request}
        )

        assert serializer.is_valid(), serializer.errors
        course = serializer.save()
        assert course.language == language

    def test_status_field_accepted(self):
        instructor = InstructorFactory()
        category = CategoryFactory(name="Cat for Status")
        request = self._make_request(instructor)

        data = {
            "title": "Draft Course",
            "description": "desc",
            "category_id": str(category.id),
            "status": Course.Status.DRAFT,
        }
        serializer = CourseCreateUpdateSerializer(
            data=data, context={"request": request}
        )

        assert serializer.is_valid(), serializer.errors

    def test_price_field_accepted(self):
        instructor = InstructorFactory()
        category = CategoryFactory(name="Cat for Price")
        request = self._make_request(instructor)

        data = {
            "title": "Paid Course",
            "description": "desc",
            "category_id": str(category.id),
            "price": "49.99",
        }
        serializer = CourseCreateUpdateSerializer(
            data=data, context={"request": request}
        )

        assert serializer.is_valid(), serializer.errors
        course = serializer.save()
        assert float(course.price) == pytest.approx(49.99)
