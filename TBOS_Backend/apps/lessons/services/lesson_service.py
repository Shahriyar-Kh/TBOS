from apps.lessons.models import Lesson


class LessonService:
    @staticmethod
    def reorder_lessons(course_id, lesson_order: list[dict]) -> None:
        """Bulk update lesson ordering. lesson_order = [{"id": ..., "order": ...}]."""
        for item in lesson_order:
            Lesson.objects.filter(
                id=item["id"], course_id=course_id
            ).update(order=item["order"])

    @staticmethod
    def get_lessons_for_course(course_id, published_only=True):
        qs = Lesson.objects.filter(course_id=course_id)
        if published_only:
            qs = qs.filter(is_published=True)
        return qs.order_by("order")
