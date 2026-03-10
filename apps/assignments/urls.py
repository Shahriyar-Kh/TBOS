from django.urls import path, include
from rest_framework.routers import DefaultRouter

from apps.assignments import views

router = DefaultRouter()
router.register(r"instructor", views.InstructorAssignmentViewSet, basename="instructor-assignments")
router.register(r"student", views.StudentAssignmentViewSet, basename="student-assignments")

urlpatterns = [
    path("", include(router.urls)),
]
