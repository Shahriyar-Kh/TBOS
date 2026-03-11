import pytest

from apps.courses.models import Category, Course, Language, LearningOutcome, Level, Requirement
from tests.factories import InstructorFactory


@pytest.mark.django_db
class TestCategoryModel:
    def test_slug_is_auto_generated(self):
        category = Category.objects.create(name="Web Development")
        assert category.slug == "web-development"

    def test_slug_is_preserved_on_resave(self):
        category = Category.objects.create(name="Data Science", slug="custom-slug")
        category.name = "Data Science Updated"
        category.save()
        assert category.slug == "custom-slug"

    def test_parent_category_relationship(self):
        parent = Category.objects.create(name="Technology")
        child = Category.objects.create(name="Programming", parent_category=parent)
        assert child.parent_category == parent
        assert child in parent.subcategories.all()

    def test_description_defaults_to_empty(self):
        category = Category.objects.create(name="Art")
        assert category.description == ""

    def test_str_returns_name(self):
        category = Category.objects.create(name="Business")
        assert str(category) == "Business"


@pytest.mark.django_db
class TestCourseModel:
    def setup_method(self):
        self.instructor = InstructorFactory()
        self.category = Category.objects.create(name="Python")
        self.level = Level.objects.create(name="Beginner")

    def test_slug_is_auto_generated(self):
        course = Course.objects.create(
            title="Python for Beginners",
            description="Learn Python",
            instructor=self.instructor,
            category=self.category,
        )
        assert course.slug == "python-for-beginners"

    def test_slug_uniqueness_appends_counter(self):
        Course.objects.create(
            title="Python for Beginners",
            description="First",
            instructor=self.instructor,
            category=self.category,
        )
        course2 = Course.objects.create(
            title="Python for Beginners",
            description="Second",
            instructor=self.instructor,
            category=self.category,
        )
        assert course2.slug == "python-for-beginners-1"

    def test_default_status_is_draft(self):
        course = Course.objects.create(
            title="Test Course Draft",
            description="desc",
            instructor=self.instructor,
        )
        assert course.status == Course.Status.DRAFT

    def test_certificate_available_defaults_false(self):
        course = Course.objects.create(
            title="A New Course Title",
            description="desc",
            instructor=self.instructor,
        )
        assert course.certificate_available is False

    def test_rating_count_defaults_to_zero(self):
        course = Course.objects.create(
            title="Rating Test Course",
            description="desc",
            instructor=self.instructor,
        )
        assert course.rating_count == 0

    def test_published_at_defaults_to_none(self):
        course = Course.objects.create(
            title="Published At Test",
            description="desc",
            instructor=self.instructor,
        )
        assert course.published_at is None

    def test_effective_price_with_discount(self):
        course = Course.objects.create(
            title="Effective Price Course",
            description="desc",
            instructor=self.instructor,
            price=100,
            discount=20,
        )
        assert float(course.effective_price) == 80.0

    def test_effective_price_for_free_course(self):
        course = Course.objects.create(
            title="Free Course Here",
            description="desc",
            instructor=self.instructor,
            price=100,
            is_free=True,
        )
        assert course.effective_price == 0

    def test_str_returns_title(self):
        course = Course.objects.create(
            title="My Course Title",
            description="desc",
            instructor=self.instructor,
        )
        assert str(course) == "My Course Title"
