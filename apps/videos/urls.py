from django.urls import path, include
from rest_framework.routers import DefaultRouter

from apps.videos import views

router = DefaultRouter()
router.register(r"public", views.PublicVideoViewSet, basename="public-videos")
router.register(r"instructor", views.InstructorVideoViewSet, basename="instructor-videos")

urlpatterns = [
    path("", include(router.urls)),
]
