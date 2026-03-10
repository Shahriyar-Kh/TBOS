from django.utils.text import slugify

from apps.courses.models import Course, Category


class CourseService:
    @staticmethod
    def create_course(instructor, validated_data: dict) -> Course:
        validated_data["instructor"] = instructor
        return Course.objects.create(**validated_data)

    @staticmethod
    def generate_unique_slug(title: str, exclude_pk=None) -> str:
        base_slug = slugify(title)
        slug = base_slug
        counter = 1
        qs = Course.objects.all()
        if exclude_pk:
            qs = qs.exclude(pk=exclude_pk)
        while qs.filter(slug=slug).exists():
            slug = f"{base_slug}-{counter}"
            counter += 1
        return slug

    @staticmethod
    def update_aggregate_stats(course: Course) -> None:
        """Recalculate denormalized stats on a course."""
        from apps.enrollments.models import Enrollment
        from apps.reviews.models import Review
        from django.db.models import Avg

        course.total_enrollments = Enrollment.objects.filter(
            course=course, is_active=True
        ).count()
        avg = Review.objects.filter(course=course).aggregate(
            avg=Avg("rating")
        )["avg"]
        course.average_rating = round(avg, 2) if avg else 0
        course.total_lessons = course.lessons.count()
        course.save(
            update_fields=[
                "total_enrollments",
                "average_rating",
                "total_lessons",
            ]
        )
