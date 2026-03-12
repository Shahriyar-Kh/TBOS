from django.urls import path, include
from rest_framework.routers import SimpleRouter

from apps.videos import views

router = SimpleRouter()
router.register(r"public", views.PublicVideoViewSet, basename="public-videos")
router.register(
    r"instructor", views.InstructorVideoViewSet, basename="instructor-videos"
)

urlpatterns = [
    path("", include(router.urls)),
    # Student endpoint: /api/v1/videos/lessons/<lesson_pk>/video/
    path(
        "lessons/<uuid:lesson_pk>/video/",
        views.LessonVideoView.as_view({"get": "retrieve"}),
        name="lesson-video-detail",
    ),
]

