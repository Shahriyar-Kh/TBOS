from django.urls import path, include
from rest_framework.routers import DefaultRouter

from apps.reviews import views

router = DefaultRouter()
router.register(r"public", views.PublicReviewViewSet, basename="public-reviews")
router.register(r"student", views.StudentReviewViewSet, basename="student-reviews")

urlpatterns = [
    path("", include(router.urls)),
]
