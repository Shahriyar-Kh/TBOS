from django.db import models

from apps.core.models import TimeStampedModel
from apps.courses.models import Course


class CourseSection(TimeStampedModel):
    """Represents a curriculum section (module) within a course."""

    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name="sections",
        db_index=True,
    )
    title = models.CharField(max_length=300)
    description = models.TextField(blank=True, default="")
    order = models.PositiveIntegerField(default=0, db_index=True)

    class Meta:
        db_table = "course_sections"
        ordering = ["order"]
        indexes = [
            models.Index(fields=["course"], name="course_sections_course_idx"),
            models.Index(fields=["order"], name="course_sections_order_idx"),
            models.Index(fields=["course", "order"], name="course_sections_co_or_idx"),
        ]

    def __str__(self):
        return f"{self.order}. {self.title} — {self.course.title}"


class Lesson(TimeStampedModel):
    """Represents a single learning unit within a course section."""

    class LessonType(models.TextChoices):
        VIDEO = "video", "Video"
        QUIZ = "quiz", "Quiz"
        ASSIGNMENT = "assignment", "Assignment"
        ARTICLE = "article", "Article"

    section = models.ForeignKey(
        CourseSection,
        on_delete=models.CASCADE,
        related_name="lessons",
        db_index=True,
    )
    title = models.CharField(max_length=300)
    description = models.TextField(blank=True, default="")
    lesson_type = models.CharField(
        max_length=20,
        choices=LessonType.choices,
        default=LessonType.VIDEO,
        db_index=True,
    )
    order = models.PositiveIntegerField(default=0, db_index=True)
    is_preview = models.BooleanField(default=False)
    duration_seconds = models.PositiveIntegerField(default=0)
    article_content = models.TextField(blank=True, default="")

    class Meta:
        db_table = "lessons"
        ordering = ["order"]
        indexes = [
            models.Index(fields=["section"], name="lessons_section_idx"),
            models.Index(fields=["order"], name="lessons_order_idx"),
            models.Index(fields=["section", "order"], name="lessons_section_order_idx"),
        ]

    def __str__(self):
        return f"{self.order}. {self.title} — {self.section.title}"
