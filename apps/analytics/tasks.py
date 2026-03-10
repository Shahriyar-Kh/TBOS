from celery import shared_task
from django.db.models import Avg, Sum, Count


@shared_task
def update_course_analytics():
    """Periodic task to recalculate aggregated course analytics."""
    from apps.analytics.models import CourseAnalytics
    from apps.courses.models import Course
    from apps.enrollments.models import Enrollment
    from apps.payments.models import Payment

    for course in Course.objects.filter(status=Course.Status.PUBLISHED):
        enrollments = Enrollment.objects.filter(course=course, is_active=True)
        analytics, _ = CourseAnalytics.objects.get_or_create(course=course)

        analytics.total_completions = enrollments.filter(
            completed_at__isnull=False
        ).count()
        analytics.avg_completion_percent = (
            enrollments.aggregate(avg=Avg("progress_percent"))["avg"] or 0
        )
        analytics.total_revenue = (
            Payment.objects.filter(
                course=course, status=Payment.Status.COMPLETED
            ).aggregate(total=Sum("amount"))["total"]
            or 0
        )
        analytics.save()
