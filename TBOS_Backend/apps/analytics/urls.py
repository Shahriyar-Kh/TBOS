from django.urls import path

from apps.analytics import views

urlpatterns = [
    path("activity/", views.RecordUserActivityView.as_view(), name="record-activity"),
    path("student/dashboard/", views.StudentDashboardView.as_view(), name="student-dashboard"),
    path("instructor/dashboard/", views.InstructorDashboardView.as_view(), name="instructor-dashboard"),
    path(
        "instructor/course/<uuid:course_id>/",
        views.InstructorCourseAnalyticsView.as_view(),
        name="instructor-course-analytics",
    ),
    path("admin/dashboard/", views.AdminDashboardView.as_view(), name="admin-dashboard"),
    path("admin/revenue/", views.AdminRevenueAnalyticsView.as_view(), name="admin-revenue"),
]