from django.urls import path, include
from rest_framework.routers import DefaultRouter

from apps.lessons import views

router = DefaultRouter()
router.register(r"public", views.PublicLessonListView, basename="public-lessons")
router.register(r"instructor", views.InstructorLessonViewSet, basename="instructor-lessons")

urlpatterns = [
    path("", include(router.urls)),
]
