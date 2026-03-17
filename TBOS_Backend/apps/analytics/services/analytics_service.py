from django.db.models import Avg, Count, Sum

from apps.analytics.models import CourseAnalytics, UserActivity
from apps.courses.models import Course


class AnalyticsService:
    @staticmethod
    def track_event(user, event_type: str, course=None, video=None, metadata=None):
        return UserActivity.objects.create(
            user=user,
            event_type=event_type,
            course=course,
            video=video,
            metadata=metadata or {},
        )

    @staticmethod
    def refresh_course_analytics(course: Course):
        analytics, _ = CourseAnalytics.objects.get_or_create(course=course)

        enrollments = course.enrollments.all()
        analytics.total_completions = enrollments.filter(
            completed_at__isnull=False
        ).count()
        agg = enrollments.aggregate(avg_progress=Avg("progress_percent"))
        analytics.avg_completion_percent = round(agg["avg_progress"] or 0, 2)

        revenue = course.orders.filter(order_status="COMPLETED").aggregate(
            total=Sum("amount")
        )
        analytics.total_revenue = revenue["total"] or 0

        views = UserActivity.objects.filter(
            course=course, event_type=UserActivity.EventType.VIDEO_WATCHED
        ).count()
        analytics.total_views = views

        analytics.save()
        return analytics
