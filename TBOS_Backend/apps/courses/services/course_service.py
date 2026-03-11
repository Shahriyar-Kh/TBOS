import logging

from django.utils import timezone
from django.utils.text import slugify

from apps.courses.models import Course, Category

logger = logging.getLogger(__name__)


class CoursePublishError(Exception):
    """Raised when a course cannot be published due to missing required fields."""
    pass


class CourseService:
    # Required fields that must be present before publishing
    PUBLISH_REQUIRED_FIELDS = ["title", "description", "featured_image", "category_id", "level_id"]

    @staticmethod
    def create_course(instructor, validated_data: dict) -> Course:
        validated_data["instructor"] = instructor
        course = Course.objects.create(**validated_data)
        logger.info("Course created: %s by instructor %s", course.slug, instructor.email)
        return course

    @staticmethod
    def update_course(course: Course, validated_data: dict) -> Course:
        for attr, value in validated_data.items():
            setattr(course, attr, value)
        course.save()
        logger.info("Course updated: %s", course.slug)
        return course

    @staticmethod
    def publish_course(course: Course, requesting_user) -> Course:
        """
        Publish a course. Validates required fields exist.
        Only the owner instructor or an admin can publish.
        """
        if requesting_user.role == "instructor" and course.instructor != requesting_user:
            raise PermissionError("You can only publish your own courses.")

        missing = []
        for field in CourseService.PUBLISH_REQUIRED_FIELDS:
            value = getattr(course, field, None)
            if not value:
                missing.append(field)

        if missing:
            raise CoursePublishError(
                f"Cannot publish course. Missing required fields: {', '.join(missing)}"
            )

        if course.status == Course.Status.ARCHIVED:
            raise CoursePublishError("Archived courses cannot be published. Please create a new course.")

        course.status = Course.Status.PUBLISHED
        course.published_at = timezone.now()
        course.save(update_fields=["status", "published_at"])
        logger.info("Course published: %s by user %s", course.slug, requesting_user.email)
        return course

    @staticmethod
    def archive_course(course: Course, requesting_user) -> Course:
        """Archive a course. Only the owner instructor or an admin can archive."""
        if requesting_user.role == "instructor" and course.instructor != requesting_user:
            raise PermissionError("You can only archive your own courses.")

        course.status = Course.Status.ARCHIVED
        course.save(update_fields=["status"])
        logger.info("Course archived: %s by user %s", course.slug, requesting_user.email)
        return course

    @staticmethod
    def get_course_by_slug(slug: str) -> Course:
        return (
            Course.objects.filter(status=Course.Status.PUBLISHED, slug=slug)
            .select_related("category", "level", "language", "instructor")
            .prefetch_related("learning_outcomes", "requirements")
            .get()
        )

    @staticmethod
    def list_public_courses(filters: dict = None):
        """Return a queryset of all published courses, optionally filtered."""
        qs = (
            Course.objects.filter(status=Course.Status.PUBLISHED)
            .select_related("category", "level", "instructor")
        )
        if filters:
            if filters.get("category"):
                qs = qs.filter(category__slug=filters["category"])
            if filters.get("level"):
                qs = qs.filter(level_id=filters["level"])
            if filters.get("language"):
                qs = qs.filter(language_id=filters["language"])
            if filters.get("is_free") is not None:
                qs = qs.filter(is_free=filters["is_free"])
        return qs

    @staticmethod
    def get_instructor_courses(instructor):
        """Return a queryset of all courses belonging to the instructor."""
        return (
            Course.objects.filter(instructor=instructor)
            .select_related("category", "level", "language")
        )

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
        from django.db.models import Avg, Count

        course.total_enrollments = Enrollment.objects.filter(
            course=course, is_active=True
        ).count()
        rating_data = Review.objects.filter(course=course).aggregate(
            avg=Avg("rating"), count=Count("id")
        )
        avg = rating_data["avg"]
        course.average_rating = round(avg, 2) if avg else 0
        course.rating_count = rating_data["count"] or 0
        course.total_lessons = course.lessons.count()
        course.save(
            update_fields=[
                "total_enrollments",
                "average_rating",
                "rating_count",
                "total_lessons",
            ]
        )
