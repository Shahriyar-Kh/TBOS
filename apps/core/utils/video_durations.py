import logging

from django.db.models import QuerySet, Sum

from apps.courses.models import Course
from apps.videos.models import Video

logger = logging.getLogger(__name__)


def video_duration(courses):
    """
    Calculate the total duration of videos for a single course, a list of courses, or a queryset of courses.

    Args:
        courses (Course | list[Course] | QuerySet[Course]): A single course object, a list of courses, or a queryset.

    Returns:
        dict | str:
            - If a single course is passed, returns a formatted string like "2h 30m".
            - If a list/queryset is passed, returns a dictionary {course_id: "2h 30m"}.
    """
    try:
        # Convert single Course instance into a list
        if isinstance(courses, Course):
            single_course = True  # Mark it for returning a string later
            courses = [courses]
        else:
            single_course = False

        # Convert QuerySet to list to avoid QuerySet behavior issues
        if isinstance(courses, QuerySet):
            courses = list(courses)

        # Handle empty input
        if not courses:
            return "0m" if single_course else {}

        course_ids = [course.id for course in courses]

        durations = {}

        # Fetch video durations from the database
        duration_data = (
            Video.objects.filter(course_id__in=course_ids)
            .values("course_id")
            .annotate(total=Sum("duration_seconds"))
            .order_by("course_id")
        )

        for item in duration_data:
            course_id = item["course_id"]
            total_seconds = item.get("total", 0) or 0
            total_minutes = total_seconds // 60
            hours = total_minutes // 60
            minutes = total_minutes % 60
            durations[course_id] = f"{hours}h {minutes}m" if hours > 0 else f"{minutes}m"

        # Return duration as a string for a single course
        if single_course:
            return durations.get(course_ids[0], "0m")

        return durations  # Return dictionary for multiple courses

    except Exception as e:
        logger.error(f"Error in video_duration: {e}")
        return "0m" if single_course else {}  # Ensure safe fallback instead of crashing
