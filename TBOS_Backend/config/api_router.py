"""
API v1 URL configuration.
All modular app URLs are aggregated under /api/v1/.
"""

from django.urls import path, include

urlpatterns = [
    path("", include("apps.accounts.urls")),
    path("courses/", include("apps.courses.urls")),
    path("lessons/", include("apps.lessons.urls")),
    path("videos/", include("apps.videos.urls")),
    path("quiz/", include("apps.quiz.urls")),
    path("assignments/", include("apps.assignments.urls")),
    path("enrollments/", include("apps.enrollments.urls")),
    path("payments/", include("apps.payments.urls")),
    path("reviews/", include("apps.reviews.urls")),
    path("analytics/", include("apps.analytics.urls")),
    path("ai/", include("apps.ai_tools.urls")),
    path("certificates/", include("apps.certificates.urls")),
    path("notifications/", include("apps.notifications.urls")),
]
