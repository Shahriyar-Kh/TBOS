import logging
from typing import Optional

from django.db.models import Avg, QuerySet
from django.utils import timezone
from django.utils.text import slugify
from rest_framework.exceptions import PermissionDenied, ValidationError

from apps.courses.models import Category, Course

logger = logging.getLogger(__name__)

# Minimum required fields before a course can be published
PUBLISH_REQUIRED_FIELDS = ("title", "description", "thumbnail", "category_id", "level_id")


class CourseService:
    # ------------------------------------------------------------------
    # Slug helpers
    # ------------------------------------------------------------------

    @staticmethod
    def generate_unique_slug(title: str, exclude_pk=None) -> str:
        """Return a unique slug derived from *title*."""
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

    # ------------------------------------------------------------------
    # CRUD
    # ------------------------------------------------------------------

    @staticmethod
    def create_course(instructor, validated_data: dict) -> Course:
        """
        Create a new course owned by *instructor*.

        The course starts in DRAFT status. The slug is auto-generated
        from the title if not provided.
        """
        validated_data.setdefault("status", Course.Status.DRAFT)
        validated_data["instructor"] = instructor
        # Ensure slug uniqueness up-front (Course.save handles it too,
        # but we generate it here so it's explicit in the service).
        title = validated_data.get("title", "")
        if title and not validated_data.get("slug"):
            validated_data["slug"] = CourseService.generate_unique_slug(title)
        course = Course.objects.create(**validated_data)
        course.refresh_from_db()
        logger.info("Course created: %s by %s", course.slug, instructor.email)
        return course

    @staticmethod
    def update_course(course: Course, validated_data: dict) -> Course:
        """
        Update mutable fields of an existing course.

        If the title changes and no explicit slug is given, regenerate
        the slug to stay in sync with the new title.
        """
        new_title = validated_data.get("title")
        if new_title and new_title != course.title and not validated_data.get("slug"):
            validated_data["slug"] = CourseService.generate_unique_slug(
                new_title, exclude_pk=course.pk
            )
        for attr, value in validated_data.items():
            setattr(course, attr, value)
        course.save()
        logger.info("Course updated: %s", course.slug)
        return course

    # ------------------------------------------------------------------
    # Workflow
    # ------------------------------------------------------------------

    @staticmethod
    def publish_course(course: Course, user) -> Course:
        """
        Transition a course from DRAFT → PUBLISHED.

        Rules:
        - Instructors can only publish their own courses.
        - Admins can publish any course.
        - Required fields must be filled before publishing.
        """
        if user.role == "instructor" and course.instructor != user:
            raise PermissionDenied("You can only publish your own courses.")

        # Validate required fields
        missing = []
        for field in PUBLISH_REQUIRED_FIELDS:
            value = getattr(course, field, None)
            if not value:
                missing.append(field.replace("_id", ""))
        if missing:
            raise ValidationError(
                {
                    "detail": (
                        f"Cannot publish. The following fields are required: "
                        f"{', '.join(missing)}."
                    )
                }
            )

        if course.status == Course.Status.ARCHIVED:
            raise ValidationError(
                {"detail": "Archived courses cannot be published directly."}
            )

        course.status = Course.Status.PUBLISHED
        course.published_at = timezone.now()
        course.save(update_fields=["status", "published_at"])
        logger.info("Course published: %s by %s", course.slug, user.email)
        return course

    @staticmethod
    def archive_course(course: Course, user) -> Course:
        """
        Transition a course to ARCHIVED status.

        Instructors can only archive their own courses; admins can archive
        any course.
        """
        if user.role == "instructor" and course.instructor != user:
            raise PermissionDenied("You can only archive your own courses.")

        if course.status == Course.Status.ARCHIVED:
            raise ValidationError({"detail": "Course is already archived."})

        course.status = Course.Status.ARCHIVED
        course.save(update_fields=["status"])
        logger.info("Course archived: %s by %s", course.slug, user.email)
        return course

    # ------------------------------------------------------------------
    # Retrieval
    # ------------------------------------------------------------------

    @staticmethod
    def get_course_by_slug(slug: str) -> Course:
        """Return a published course by its slug, or raise DoesNotExist."""
        return (
            Course.objects.filter(status=Course.Status.PUBLISHED, slug=slug)
            .select_related("category", "level", "language", "instructor")
            .prefetch_related("learning_outcomes", "requirements")
            .get()
        )

    @staticmethod
    def list_public_courses(filters: Optional[dict] = None) -> QuerySet:
        """
        Return a queryset of published courses, optionally filtered.

        Supported filter keys:
            category   – category slug
            level      – level pk
            language   – language pk
            min_price  – minimum price
            max_price  – maximum price
            search     – title / subtitle search (icontains)
        """
        qs = (
            Course.objects.filter(status=Course.Status.PUBLISHED)
            .select_related("category", "level", "instructor")
            .only(
                "id", "title", "slug", "subtitle", "thumbnail", "featured_image",
                "price", "discount_price", "discount", "is_free", "status",
                "average_rating", "rating_count", "total_enrollments",
                "duration_hours", "total_lessons", "created_at",
                "category__id", "category__name", "category__icon", "category__slug",
                "level__id", "level__name",
                "instructor__id", "instructor__first_name", "instructor__last_name",
            )
        )
        if not filters:
            return qs

        if category := filters.get("category"):
            qs = qs.filter(category__slug=category)
        if level := filters.get("level"):
            qs = qs.filter(level__id=level)
        if language := filters.get("language"):
            qs = qs.filter(language__id=language)
        if min_price := filters.get("min_price"):
            qs = qs.filter(price__gte=min_price)
        if max_price := filters.get("max_price"):
            qs = qs.filter(price__lte=max_price)
        if search := filters.get("search"):
            from django.db.models import Q
            qs = qs.filter(
                Q(title__icontains=search) | Q(subtitle__icontains=search)
            )
        return qs

    @staticmethod
    def get_instructor_courses(instructor) -> QuerySet:
        """Return all courses (any status) owned by *instructor*."""
        return (
            Course.objects.filter(instructor=instructor)
            .select_related("category", "level", "language")
            .order_by("-created_at")
        )

    # ------------------------------------------------------------------
    # Aggregate stats (called by signals / periodic tasks)
    # ------------------------------------------------------------------

    @staticmethod
    def update_aggregate_stats(course: Course) -> None:
        """Recalculate denormalised stats (enrollments, ratings, lessons)."""
        from django.db.models import Avg, Count

        from apps.enrollments.models import Enrollment
        from apps.lessons.models import Lesson
        from apps.reviews.models import Review

        course.total_enrollments = Enrollment.objects.filter(
            course=course, is_active=True
        ).count()
        review_agg = Review.objects.filter(course=course).aggregate(
            avg=Avg("rating"), count=Count("id")
        )
        course.average_rating = round(review_agg["avg"], 2) if review_agg["avg"] else 0
        course.rating_count = review_agg["count"] or 0
        course.total_lessons = Lesson.objects.filter(section__course=course).count()
        course.save(
            update_fields=[
                "total_enrollments",
                "average_rating",
                "rating_count",
                "total_lessons",
            ]
        )
