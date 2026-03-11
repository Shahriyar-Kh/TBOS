<<<<<<< HEAD
"""Tests for courses models."""
import pytest
from django.utils.text import slugify

from apps.courses.models import Category, Course, Language, Level, LearningOutcome, Requirement


@pytest.fixture
def category(db):
    return Category.objects.create(name="Programming")


@pytest.fixture
def level(db):
    return Level.objects.create(name="Beginner")


@pytest.fixture
def language(db):
    return Language.objects.create(name="English")


@pytest.fixture
def course(db, instructor_user, category, level, language):
    return Course.objects.create(
        title="Python for Beginners",
        description="Learn Python from scratch.",
        instructor=instructor_user,
        category=category,
        level=level,
        language=language,
        price="49.99",
    )


class TestCourseSlugGeneration:
    def test_slug_generated_from_title(self, course):
        assert course.slug == "python-for-beginners"

    def test_slug_unique_suffix_on_conflict(self, db, instructor_user, category):
        c1 = Course.objects.create(
            title="Python Course",
            description="First",
            instructor=instructor_user,
            category=category,
            price="10",
        )
        c2 = Course.objects.create(
            title="Python Course",
            description="Second",
            instructor=instructor_user,
            category=category,
            price="10",
        )
        assert c1.slug == "python-course"
        assert c2.slug == "python-course-1"

    def test_slug_not_regenerated_on_save(self, course):
        original_slug = course.slug
        course.subtitle = "Updated subtitle"
        course.save()
        course.refresh_from_db()
        assert course.slug == original_slug


class TestCourseStatus:
    def test_default_status_is_draft(self, course):
        assert course.status == Course.Status.DRAFT

    def test_status_choices(self):
        choices = [c[0] for c in Course.Status.choices]
        assert "draft" in choices
        assert "published" in choices
        assert "archived" in choices


class TestCourseEffectivePrice:
    def test_effective_price_with_discount_price(self, course):
        from decimal import Decimal
        course.price = Decimal("100.00")
        course.discount_price = Decimal("79.99")
        assert float(course.effective_price) == 79.99

    def test_effective_price_falls_back_to_discount_pct(self, course):
        from decimal import Decimal
        course.price = Decimal("100.00")
        course.discount_price = Decimal("0.00")
        course.discount = Decimal("10.00")
        assert float(course.effective_price) == 90.0

    def test_effective_price_zero_for_free_course(self, course):
        from decimal import Decimal
        course.is_free = True
        course.price = Decimal("99.00")
        assert course.effective_price == Decimal("0")


class TestCourseRelatedModels:
    def test_learning_outcome_created(self, course):
        lo = LearningOutcome.objects.create(course=course, text="Build REST APIs", order=1)
        assert lo.course == course
        assert lo in course.learning_outcomes.all()

    def test_requirement_created(self, course):
        req = Requirement.objects.create(course=course, text="Basic Python knowledge", order=1)
        assert req.course == course
        assert req in course.requirements.all()


class TestCategoryModel:
    def test_category_str(self, category):
        assert str(category) == "Programming"

    def test_category_slug_generated(self, category):
        assert category.slug == "programming"
=======
import uuid

import pytest
from django.db import IntegrityError

from apps.courses.models import Category, Course, Language, LearningOutcome, Level, Requirement
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
class TestCategoryModel:
    def test_category_creation(self):
        category = CategoryFactory(name="Web Development")

        assert category.pk is not None
        assert category.name == "Web Development"

    def test_slug_auto_generated_from_name(self):
        category = CategoryFactory(name="Data Science")

        assert category.slug == "data-science"

    def test_slug_not_overwritten_if_already_set(self):
        category = CategoryFactory(name="Machine Learning", slug="ml-custom")

        assert category.slug == "ml-custom"

    def test_category_name_must_be_unique(self):
        CategoryFactory(name="Unique Category")

        with pytest.raises(IntegrityError):
            CategoryFactory(name="Unique Category")

    def test_category_uuid_primary_key(self):
        category = CategoryFactory()

        assert isinstance(category.id, uuid.UUID)

    def test_category_str_returns_name(self):
        category = CategoryFactory(name="Backend Dev")

        assert str(category) == "Backend Dev"

    def test_category_icon_defaults_to_empty_string(self):
        category = Category.objects.create(name="No Icon")

        assert category.icon == ""

    def test_category_ordering_by_name(self):
        CategoryFactory(name="Zebra Category")
        CategoryFactory(name="Alpha Category")

        categories = list(Category.objects.all())
        names = [c.name for c in categories]
        assert names == sorted(names)


@pytest.mark.django_db
class TestLevelModel:
    def test_level_creation(self):
        level = LevelFactory(name="Beginner")

        assert level.pk is not None
        assert level.name == "Beginner"

    def test_level_name_must_be_unique(self):
        LevelFactory(name="Advanced")

        with pytest.raises(IntegrityError):
            LevelFactory(name="Advanced")

    def test_level_uuid_primary_key(self):
        level = LevelFactory()

        assert isinstance(level.id, uuid.UUID)

    def test_level_str_returns_name(self):
        level = LevelFactory(name="Intermediate")

        assert str(level) == "Intermediate"


@pytest.mark.django_db
class TestLanguageModel:
    def test_language_creation(self):
        language = LanguageFactory(name="English")

        assert language.pk is not None
        assert language.name == "English"

    def test_language_name_must_be_unique(self):
        LanguageFactory(name="Persian")

        with pytest.raises(IntegrityError):
            LanguageFactory(name="Persian")

    def test_language_uuid_primary_key(self):
        language = LanguageFactory()

        assert isinstance(language.id, uuid.UUID)

    def test_language_str_returns_name(self):
        language = LanguageFactory(name="Farsi")

        assert str(language) == "Farsi"


@pytest.mark.django_db
class TestCourseModel:
    def test_course_creation(self):
        course = CourseFactory(title="Django for Beginners")

        assert course.pk is not None
        assert course.title == "Django for Beginners"

    def test_course_uuid_primary_key(self):
        course = CourseFactory()

        assert isinstance(course.id, uuid.UUID)

    def test_default_status_is_draft(self):
        course = CourseFactory()

        assert course.status == Course.Status.DRAFT

    def test_slug_auto_generated_from_title(self):
        course = CourseFactory(title="Python REST API")

        assert course.slug == "python-rest-api"

    def test_slug_is_unique_when_conflict_exists(self):
        CourseFactory(title="My Course")
        course2 = CourseFactory(title="My Course")

        assert course2.slug == "my-course-1"

    def test_slug_unique_counter_increments(self):
        CourseFactory(title="Duplicate Title")
        CourseFactory(title="Duplicate Title")
        course3 = CourseFactory(title="Duplicate Title")

        assert course3.slug == "duplicate-title-2"

    def test_slug_not_overwritten_if_provided(self):
        course = CourseFactory(title="Django Advanced", slug="custom-slug")

        assert course.slug == "custom-slug"

    def test_course_belongs_to_instructor(self):
        instructor = InstructorFactory()
        course = CourseFactory(instructor=instructor)

        assert course.instructor == instructor
        assert course in instructor.taught_courses.all()

    def test_course_belongs_to_category(self):
        category = CategoryFactory(name="Programming")
        course = CourseFactory(category=category)

        assert course.category == category
        assert course in category.courses.all()

    def test_course_default_price_is_zero(self):
        course = Course.objects.create(
            instructor=InstructorFactory(),
            category=CategoryFactory(name="Cat for Price Test"),
            title="Free Course",
            description="A free course",
        )

        assert course.price == 0

    def test_course_str_returns_title(self):
        course = CourseFactory(title="My Test Course")

        assert str(course) == "My Test Course"

    def test_effective_price_with_discount(self):
        course = CourseFactory(price=100, discount=20)

        assert course.effective_price == 80

    def test_effective_price_is_zero_for_free_course(self):
        course = CourseFactory(price=100, is_free=True)

        assert course.effective_price == 0

    def test_effective_price_without_discount(self):
        course = CourseFactory(price=49.99, discount=0)

        assert float(course.effective_price) == pytest.approx(49.99)

    def test_course_status_choices(self):
        course = CourseFactory()

        course.status = Course.Status.PUBLISHED
        course.save(update_fields=["status"])
        course.refresh_from_db()
        assert course.status == Course.Status.PUBLISHED

        course.status = Course.Status.ARCHIVED
        course.save(update_fields=["status"])
        course.refresh_from_db()
        assert course.status == Course.Status.ARCHIVED

    def test_course_level_is_nullable(self):
        course = Course.objects.create(
            instructor=InstructorFactory(),
            category=CategoryFactory(name="Cat Nullable Level"),
            title="No Level Course",
            description="No level",
            level=None,
        )

        assert course.level is None

    def test_course_language_is_nullable(self):
        course = Course.objects.create(
            instructor=InstructorFactory(),
            category=CategoryFactory(name="Cat Nullable Language"),
            title="No Language Course",
            description="No language",
            language=None,
        )

        assert course.language is None

    def test_course_category_set_null_on_category_delete(self):
        category = CategoryFactory(name="To Delete Category")
        course = CourseFactory(category=category)
        category.delete()
        course.refresh_from_db()

        assert course.category is None


@pytest.mark.django_db
class TestLearningOutcomeModel:
    def test_learning_outcome_creation(self):
        outcome = LearningOutcomeFactory(text="Understand Django ORM")

        assert outcome.pk is not None
        assert outcome.text == "Understand Django ORM"

    def test_learning_outcome_belongs_to_course(self):
        course = CourseFactory()
        outcome = LearningOutcomeFactory(course=course)

        assert outcome.course == course
        assert outcome in course.learning_outcomes.all()

    def test_learning_outcome_str(self):
        outcome = LearningOutcomeFactory(text="Build REST APIs")

        assert str(outcome) == "Build REST APIs"

    def test_learning_outcomes_ordered_by_order(self):
        course = CourseFactory()
        LearningOutcomeFactory(course=course, text="Third", order=2)
        LearningOutcomeFactory(course=course, text="First", order=0)
        LearningOutcomeFactory(course=course, text="Second", order=1)

        outcomes = list(course.learning_outcomes.all())
        assert [o.order for o in outcomes] == [0, 1, 2]


@pytest.mark.django_db
class TestRequirementModel:
    def test_requirement_creation(self):
        req = RequirementFactory(text="Basic Python knowledge")

        assert req.pk is not None
        assert req.text == "Basic Python knowledge"

    def test_requirement_belongs_to_course(self):
        course = CourseFactory()
        req = RequirementFactory(course=course)

        assert req.course == course
        assert req in course.requirements.all()

    def test_requirement_str(self):
        req = RequirementFactory(text="Know HTML basics")

        assert str(req) == "Know HTML basics"

    def test_requirements_ordered_by_order(self):
        course = CourseFactory()
        RequirementFactory(course=course, text="Third", order=2)
        RequirementFactory(course=course, text="First", order=0)
        RequirementFactory(course=course, text="Second", order=1)

        reqs = list(course.requirements.all())
        assert [r.order for r in reqs] == [0, 1, 2]
>>>>>>> 36e9d9d1ebb34bf8b78a481d28bf7cf2ca6f757e
