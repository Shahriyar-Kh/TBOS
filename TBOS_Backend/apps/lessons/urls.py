from django.urls import include, path
from rest_framework.routers import SimpleRouter

from apps.lessons import views

router = SimpleRouter()
router.register(r"public", views.PublicLessonListView, basename="public-lessons")
router.register(
    r"instructor/sections",
    views.InstructorSectionViewSet,
    basename="instructor-sections",
)
router.register(
    r"instructor/lessons",
    views.InstructorLessonViewSet,
    basename="instructor-lessons",
)

urlpatterns = [
    path("", include(router.urls)),
    # Student video endpoint: GET /api/v1/lessons/{lesson_pk}/video/
    path(
        "<uuid:lesson_pk>/video/",
        include("apps.videos.urls_lesson"),
    ),
]
