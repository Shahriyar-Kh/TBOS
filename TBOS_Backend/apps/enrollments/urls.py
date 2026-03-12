from django.urls import path, include
from rest_framework.routers import SimpleRouter

from apps.enrollments import views

router = SimpleRouter()
router.register(r"student", views.StudentEnrollmentViewSet, basename="student-enrollments")
router.register(r"admin", views.AdminEnrollmentViewSet, basename="admin-enrollments")
router.register(r"instructor", views.InstructorEnrollmentViewSet, basename="instructor-enrollments")

urlpatterns = [
    path("", include(router.urls)),
]
