from django.urls import path, include
from rest_framework.routers import DefaultRouter

from apps.analytics import views

router = DefaultRouter()
router.register(
    r"instructor", views.InstructorCourseAnalyticsViewSet, basename="instructor-analytics"
)
router.register(
    r"admin/activities", views.AdminUserActivityViewSet, basename="admin-activities"
)

urlpatterns = [
    path("track/", views.TrackActivityView.as_view(), name="track-activity"),
    path(
        "admin/platform-stats/",
        views.AdminPlatformStatsView.as_view(),
        name="platform-stats",
    ),
    path("", include(router.urls)),
]
