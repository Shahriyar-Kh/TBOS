"""
URL Configuration — TBOS
API-only with Swagger documentation.
"""

from django.conf import settings
from django.urls import path, include
from django.conf.urls.static import static
from drf_spectacular.utils import extend_schema
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
    SpectacularRedocView,
)
from rest_framework.response import Response
from rest_framework.views import APIView


class APIRootView(APIView):
    """GET /api/v1/ — API index listing all available endpoints."""

    permission_classes = []
    authentication_classes = []

    @extend_schema(
        tags=["Accounts"],
        summary="API root index",
        request=None,
        auth=[],
        responses={200: {"description": "API root metadata and endpoint index."}},
    )
    def get(self, request):
        return Response(
            {
                "name": "TechBuilt Open School API",
                "version": "v1",
                "docs": "/api/docs/",
                "schema": "/api/schema/",
                "endpoints": {
                    "auth": "/api/v1/auth/",
                    "admin_users": "/api/v1/admin/users/",
                    "courses": "/api/v1/courses/",
                    "lessons": "/api/v1/lessons/",
                    "videos": "/api/v1/videos/",
                    "quiz": "/api/v1/quiz/",
                    "assignments": "/api/v1/assignments/",
                    "enrollments": "/api/v1/enrollments/",
                    "payments": "/api/v1/payments/",
                    "reviews": "/api/v1/reviews/",
                    "analytics": "/api/v1/analytics/",
                    "analytics_ws_dashboard": "/ws/analytics/dashboard/?token=<jwt>",
                    "analytics_ws_course": "/ws/analytics/course/{course_id}/?token=<jwt>",
                    "ai_tools": "/api/v1/ai/",
                    "certificates": "/api/v1/certificates/",
                    "notifications": "/api/v1/notifications/",
                },
            }
        )


urlpatterns = [
    # API v1
    path("api/v1/", APIRootView.as_view(), name="api-root"),
    path("api/v1/", include(("config.api_router", "api"), namespace="v1")),

    # API Documentation
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("api/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
