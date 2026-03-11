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
