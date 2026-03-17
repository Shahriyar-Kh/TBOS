from django.db.models import Count, Sum
from django.shortcuts import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from apps.analytics.models import CourseAnalytics
from apps.analytics.serializers import (
    AdminAnalyticsSerializer,
    CourseAnalyticsSerializer,
    InstructorAnalyticsSerializer,
    RevenueAnalyticsSerializer,
    StudentAnalyticsSerializer,
    TrackActivitySerializer,
)
from apps.analytics.services.analytics_service import (
    generate_learning_insights,
    get_admin_dashboard,
    get_instructor_dashboard,
    get_student_dashboard,
    record_user_activity,
    update_course_analytics,
)
from apps.core.exceptions import api_error, api_success
from apps.core.permissions import IsAdmin, IsAdminOrInstructor, IsStudent
from apps.courses.models import Course
from apps.payments.models import Order


class StudentDashboardView(APIView):
    permission_classes = [IsAuthenticated, IsStudent]

    def get(self, request):
        data = get_student_dashboard(request.user)
        payload = {
            "overview": StudentAnalyticsSerializer(data["overview"]).data,
            "insights": data["insights"],
        }
        return api_success(data=payload, message="Student analytics fetched successfully.")


class InstructorDashboardView(APIView):
    permission_classes = [IsAuthenticated, IsAdminOrInstructor]

    def get(self, request):
        if request.user.role == "admin":
            return api_error(
                errors={"detail": "Admin users must use admin analytics endpoints."},
                message="Invalid role for this endpoint.",
                status_code=403,
            )
        data = get_instructor_dashboard(request.user)
        serializer = InstructorAnalyticsSerializer(data)
        return api_success(data=serializer.data, message="Instructor analytics fetched successfully.")


class InstructorCourseAnalyticsView(APIView):
    permission_classes = [IsAuthenticated, IsAdminOrInstructor]

    def get(self, request, course_id):
        course = get_object_or_404(Course.objects.select_related("instructor"), id=course_id)
        if request.user.role == "instructor" and course.instructor_id != request.user.id:
            return api_error(
                errors={"detail": "You can only access analytics for your own courses."},
                message="Forbidden.",
                status_code=403,
            )

        update_course_analytics(course_id=course.id)
        analytics = (
            CourseAnalytics.objects.filter(course=course)
            .select_related("course")
            .order_by("-last_updated")
            .first()
        )
        if analytics is None:
            return api_success(data={}, message="No analytics available for this course yet.")

        serializer = CourseAnalyticsSerializer(analytics)
        return api_success(data=serializer.data, message="Course analytics fetched successfully.")


class AdminDashboardView(APIView):
    permission_classes = [IsAuthenticated, IsAdmin]

    def get(self, request):
        start_date = request.query_params.get("start_date")
        end_date = request.query_params.get("end_date")

        data = get_admin_dashboard(start_date=start_date or None, end_date=end_date or None)
        serializer = AdminAnalyticsSerializer(data)

        return api_success(
            data={
                **serializer.data,
                "insights": generate_learning_insights(),
            },
            message="Admin analytics fetched successfully.",
        )


class AdminRevenueAnalyticsView(APIView):
    permission_classes = [IsAuthenticated, IsAdmin]

    def get(self, request):
        start_date = request.query_params.get("start_date")
        end_date = request.query_params.get("end_date")

        revenue_qs = Order.objects.filter(order_status=Order.OrderStatus.COMPLETED)
        if start_date:
            revenue_qs = revenue_qs.filter(created_at__date__gte=start_date)
        if end_date:
            revenue_qs = revenue_qs.filter(created_at__date__lte=end_date)

        aggregate = revenue_qs.aggregate(total_revenue=Sum("amount"), total_orders=Count("id"))
        total_revenue = aggregate["total_revenue"] or 0
        total_orders = aggregate["total_orders"] or 0

        payload = RevenueAnalyticsSerializer(
            {
                "start_date": start_date,
                "end_date": end_date,
                "total_revenue": total_revenue,
                "total_orders": total_orders,
                "average_order_value": (total_revenue / total_orders) if total_orders else 0,
            }
        ).data

        return api_success(data=payload, message="Revenue analytics fetched successfully.")


class RecordUserActivityView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = TrackActivitySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        activity = record_user_activity(
            user=request.user,
            activity_type=serializer.validated_data["activity_type"],
            reference_id=serializer.validated_data.get("reference_id"),
        )

        return api_success(
            data={"activity_id": str(activity.id)},
            message="User activity recorded successfully.",
            status_code=201,
        )
