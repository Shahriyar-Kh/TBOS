from django.conf import settings
from django.db import models
from django.utils.text import slugify

from apps.core.models import TimeStampedModel


class CourseCategory(TimeStampedModel):
    """Hierarchical course category (supports parent/child nesting)."""

    name = models.CharField(max_length=200, unique=True, db_index=True)
    slug = models.SlugField(max_length=220, unique=True, blank=True)
    icon = models.CharField(max_length=200, blank=True, default="")
    description = models.TextField(blank=True, default="")
    parent = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="children",
    )

    class Meta:
        db_table = "course_categories"
        verbose_name = "Course Category"
        verbose_name_plural = "Course Categories"
        ordering = ["name"]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


# Keep backward-compatible alias used by other apps (e.g. analytics, reviews)
class Category(TimeStampedModel):
    name = models.CharField(max_length=200, unique=True, db_index=True)
    icon = models.CharField(max_length=200, blank=True, default="")
    slug = models.SlugField(max_length=220, unique=True, blank=True)

    class Meta:
        db_table = "categories"
        verbose_name_plural = "categories"
        ordering = ["name"]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class CourseLevel(TimeStampedModel):
    """Difficulty level for a course (e.g. Beginner, Intermediate, Advanced)."""

    name = models.CharField(max_length=100, unique=True)

    class Meta:
        db_table = "course_levels"
        verbose_name = "Course Level"

    def __str__(self):
        return self.name


class Level(TimeStampedModel):
    name = models.CharField(max_length=100, unique=True)

    class Meta:
        db_table = "levels"

    def __str__(self):
        return self.name


class CourseLanguage(TimeStampedModel):
    """Language in which a course is taught."""

    name = models.CharField(max_length=100, unique=True)

    class Meta:
        db_table = "course_languages"
        verbose_name = "Course Language"

    def __str__(self):
        return self.name


class Language(TimeStampedModel):
    name = models.CharField(max_length=100, unique=True)

    class Meta:
        db_table = "languages"

    def __str__(self):
        return self.name


class Course(TimeStampedModel):
    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        PUBLISHED = "published", "Published"
        ARCHIVED = "archived", "Archived"

    instructor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="taught_courses",
        db_index=True,
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        related_name="courses",
        db_index=True,
    )
    level = models.ForeignKey(
        Level,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="courses",
    )
    language = models.ForeignKey(
        Language,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="courses",
    )
    title = models.CharField(max_length=500, db_index=True)
    slug = models.SlugField(max_length=550, unique=True, blank=True, db_index=True)
    subtitle = models.CharField(max_length=500, blank=True, default="")
    description = models.TextField()
    # thumbnail stores a URL (Cloudinary / S3) to the course cover image
    thumbnail = models.URLField(max_length=500, blank=True, default="")
    # featured_image kept for backward compatibility with existing code
    featured_image = models.URLField(max_length=500, blank=True, default="")
    promo_video_url = models.URLField(max_length=500, blank=True, default="")
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    # discount_price is an absolute discounted price (0 means no discount)
    discount_price = models.DecimalField(
        max_digits=10, decimal_places=2, default=0.00,
        help_text="Absolute discounted price. Must be less than price."
    )
    # discount kept for backward compat (percentage-based)
    discount = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT,
        db_index=True,
    )
    is_free = models.BooleanField(default=False, db_index=True)
    certificate_available = models.BooleanField(default=False)
    duration_hours = models.PositiveIntegerField(
        default=0, help_text="Estimated total duration in hours"
    )
    total_lessons = models.PositiveIntegerField(default=0)
    total_enrollments = models.PositiveIntegerField(default=0)
    average_rating = models.DecimalField(
        max_digits=3, decimal_places=2, default=0.00
    )
    rating_count = models.PositiveIntegerField(default=0)
    published_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "courses"
        indexes = [
            models.Index(fields=["slug"], name="courses_slug_idx"),
            models.Index(fields=["status", "created_at"]),
            models.Index(fields=["instructor", "status"]),
            models.Index(fields=["category", "status"]),
        ]

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.title)
            slug = base_slug
            counter = 1
            while Course.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title

    @property
    def effective_price(self):
        from decimal import Decimal
        try:
            price = Decimal(str(self.price))
            discount_price = Decimal(str(self.discount_price))
            discount = Decimal(str(self.discount))
        except Exception:
            return 0
        if self.is_free:
            return Decimal("0")
        if discount_price and discount_price < price:
            return discount_price
        if discount:
            return max(price - (price * discount / Decimal("100")), Decimal("0"))
        return price


class LearningOutcome(TimeStampedModel):
    course = models.ForeignKey(
        Course, on_delete=models.CASCADE, related_name="learning_outcomes"
    )
    text = models.CharField(max_length=500)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = "learning_outcomes"
        ordering = ["order"]

    def __str__(self):
        return self.text


# Spec alias
CourseLearningOutcome = LearningOutcome


class Requirement(TimeStampedModel):
    course = models.ForeignKey(
        Course, on_delete=models.CASCADE, related_name="requirements"
    )
    text = models.CharField(max_length=500)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = "course_requirements"
        ordering = ["order"]

    def __str__(self):
        return self.text


# Spec alias
CourseRequirement = Requirement
