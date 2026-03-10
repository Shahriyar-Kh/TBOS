from django.urls import path, include
from rest_framework.routers import DefaultRouter

from apps.quiz import views

router = DefaultRouter()
router.register(r"instructor/quizzes", views.InstructorQuizViewSet, basename="instructor-quizzes")
router.register(r"instructor/questions", views.InstructorQuestionViewSet, basename="instructor-questions")
router.register(r"instructor/options", views.InstructorOptionViewSet, basename="instructor-options")
router.register(r"student", views.StudentQuizViewSet, basename="student-quizzes")

urlpatterns = [
    path("", include(router.urls)),
]
