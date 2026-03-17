from django.contrib.auth import get_user_model
from django.db.models import Sum
from rest_framework import generics, status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.pagination import StandardPagination
from apps.core.permissions import IsAdmin, IsAdminOrInstructor
from apps.analytics.models import CourseAnalytics, UserActivity
from apps.analytics.serializers import (
    CourseAnalyticsSerializer,
    PlatformStatsSerializer,
    TrackActivitySerializer,
    UserActivitySerializer,
)
from apps.courses.models import Course
from apps.enrollments.models import Enrollment
from apps.payments.models import Order

User = get_user_model()


class TrackActivityView(APIView):
    """
    POST /api/v1/analytics/track/
    Log a user activity event.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = TrackActivitySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        UserActivity.objects.create(
            user=request.user,
            event_type=data["event_type"],
            course_id=data.get("course_id"),
            video_id=data.get("video_id"),
            metadata=data.get("metadata", {}),
        )
        return Response(
            {"success": True}, status=status.HTTP_201_CREATED
        )


class InstructorCourseAnalyticsViewSet(viewsets.ReadOnlyModelViewSet):
    """
    /api/v1/analytics/instructor/
    Instructor analytics for their courses.
    """
    serializer_class = CourseAnalyticsSerializer
    permission_classes = [IsAuthenticated, IsAdminOrInstructor]

    def get_queryset(self):
        user = self.request.user
        qs = CourseAnalytics.objects.select_related("course")
        if user.role == "instructor":
            qs = qs.filter(course__instructor=user)
        return qs


class AdminPlatformStatsView(APIView):
    """
    GET /api/v1/analytics/admin/platform-stats/
    High-level platform metrics.
    """
    permission_classes = [IsAuthenticated, IsAdmin]

    def get(self, request):
        stats = {
            "total_users": User.objects.count(),
            "total_students": User.objects.filter(role="student").count(),
            "total_instructors": User.objects.filter(role="instructor").count(),
            "total_courses": Course.objects.filter(
                status=Course.Status.PUBLISHED
            ).count(),
            "total_enrollments": Enrollment.objects.filter(is_active=True).count(),
            "total_revenue": Order.objects.filter(
                order_status=Order.OrderStatus.COMPLETED
            ).aggregate(total=Sum("amount"))["total"]
            or 0,
        }
        return Response(PlatformStatsSerializer(stats).data)


class AdminUserActivityViewSet(viewsets.ReadOnlyModelViewSet):
    """
    /api/v1/analytics/admin/activities/
    """
    serializer_class = UserActivitySerializer
    permission_classes = [IsAuthenticated, IsAdmin]
    pagination_class = StandardPagination

    def get_queryset(self):
        qs = UserActivity.objects.select_related("user", "course")
        user_id = self.request.query_params.get("user")
        if user_id:
            qs = qs.filter(user_id=user_id)
        event_type = self.request.query_params.get("event_type")
        if event_type:
            qs = qs.filter(event_type=event_type)
        return qs
