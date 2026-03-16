from django.urls import path, include
from rest_framework.routers import SimpleRouter

from apps.reviews import views

router = SimpleRouter()
router.register(r"public", views.PublicReviewViewSet, basename="public-reviews")
router.register(r"student", views.StudentReviewViewSet, basename="student-reviews")
router.register(r"instructor", views.InstructorReviewViewSet, basename="instructor-reviews")
router.register(r"admin", views.AdminReviewViewSet, basename="admin-reviews")

urlpatterns = [
    path("", include(router.urls)),
]
