from django.shortcuts import get_object_or_404

from apps.courses.models import Course
from apps.lessons.models import CourseSection, Lesson


class LessonService:
    # ──────────────────────────────────────────────────────────────
    # Section CRUD
    # ──────────────────────────────────────────────────────────────

    @staticmethod
    def create_section(course: Course, validated_data: dict) -> CourseSection:
        """Create a new section for the given course."""
        validated_data.pop("course", None)
        return CourseSection.objects.create(course=course, **validated_data)

    @staticmethod
    def update_section(section: CourseSection, validated_data: dict) -> CourseSection:
        """Update an existing section's mutable fields."""
        for attr, value in validated_data.items():
            setattr(section, attr, value)
        section.save()
        return section

    @staticmethod
    def delete_section(section: CourseSection) -> None:
        """Delete a section and all its lessons (cascade)."""
        section.delete()

    @staticmethod
    def reorder_sections(course_id, section_order: list[dict]) -> None:
        """Bulk update section ordering.

        section_order = [{"id": <uuid>, "order": <int>}, ...]
        """
        for item in section_order:
            CourseSection.objects.filter(
                id=item["id"], course_id=course_id
            ).update(order=item["order"])

    # ──────────────────────────────────────────────────────────────
    # Lesson CRUD
    # ──────────────────────────────────────────────────────────────

    @staticmethod
    def create_lesson(section: CourseSection, validated_data: dict) -> Lesson:
        """Create a new lesson inside the given section."""
        validated_data.pop("section", None)
        return Lesson.objects.create(section=section, **validated_data)

    @staticmethod
    def update_lesson(lesson: Lesson, validated_data: dict) -> Lesson:
        """Update an existing lesson."""
        for attr, value in validated_data.items():
            setattr(lesson, attr, value)
        lesson.save()
        return lesson

    @staticmethod
    def delete_lesson(lesson: Lesson) -> None:
        """Delete a lesson."""
        lesson.delete()

    @staticmethod
    def reorder_lessons(section_id, lesson_order: list[dict]) -> None:
        """Bulk update lesson ordering.

        lesson_order = [{"id": <uuid>, "order": <int>}, ...]
        """
        for item in lesson_order:
            Lesson.objects.filter(
                id=item["id"], section_id=section_id
            ).update(order=item["order"])

    # ──────────────────────────────────────────────────────────────
    # Curriculum retrieval
    # ──────────────────────────────────────────────────────────────

    @staticmethod
    def get_course_curriculum(slug: str) -> Course:
        """Return the course with all sections and lessons prefetched."""
        return (
            Course.objects.filter(slug=slug)
            .prefetch_related(
                "sections",
                "sections__lessons",
            )
            .select_related("instructor")
            .get()
        )

    # ──────────────────────────────────────────────────────────────
    # Legacy helpers (kept for backward compatibility)
    # ──────────────────────────────────────────────────────────────

    @staticmethod
    def get_lessons_for_course(course_id, published_only=False):
        """Return all lessons for a course, traversing sections."""
        qs = Lesson.objects.filter(section__course_id=course_id)
        if published_only:
            qs = qs.filter(is_preview=False)
        return qs.select_related("section").order_by("section__order", "order")

