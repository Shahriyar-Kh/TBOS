from django.conf import settings
from django.db import models
from django.utils.text import slugify

from apps.core.models import TimeStampedModel


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


class Level(TimeStampedModel):
    name = models.CharField(max_length=100, unique=True)

    class Meta:
        db_table = "levels"

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
    slug = models.SlugField(max_length=550, unique=True, blank=True)
    subtitle = models.CharField(max_length=500, blank=True, default="")
    description = models.TextField()
    featured_image = models.URLField(max_length=500, blank=True, default="")
    promo_video_url = models.URLField(max_length=500, blank=True, default="")
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    discount = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT,
        db_index=True,
    )
    is_free = models.BooleanField(default=False, db_index=True)
    duration_hours = models.PositiveIntegerField(default=0, help_text="Total hours")
    total_lessons = models.PositiveIntegerField(default=0)
    total_enrollments = models.PositiveIntegerField(default=0)
    average_rating = models.DecimalField(
        max_digits=3, decimal_places=2, default=0.00
    )

    class Meta:
        db_table = "courses"
        indexes = [
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
        if self.is_free:
            return 0
        return max(self.price - (self.price * self.discount / 100), 0)


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
