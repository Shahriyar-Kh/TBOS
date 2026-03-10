from django.urls import path, include
from rest_framework.routers import DefaultRouter

from apps.enrollments import views

router = DefaultRouter()
router.register(r"student", views.StudentEnrollmentViewSet, basename="student-enrollments")
router.register(r"admin", views.AdminEnrollmentViewSet, basename="admin-enrollments")
router.register(r"instructor", views.InstructorEnrollmentViewSet, basename="instructor-enrollments")

urlpatterns = [
    path("", include(router.urls)),
]
