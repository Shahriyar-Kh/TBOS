from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.db.models import Count

from apps.core.permissions import IsAdminOrInstructor
from apps.lessons.models import Lesson
from apps.lessons.serializers import LessonSerializer, LessonListSerializer


class PublicLessonListView(viewsets.ReadOnlyModelViewSet):
    """
    GET /api/v1/lessons/?course={course_id}
    Public read-only listing of published lessons for a course.
    """
    serializer_class = LessonListSerializer
    permission_classes = [AllowAny]
    pagination_class = None

    def get_queryset(self):
        qs = Lesson.objects.filter(is_published=True).annotate(
            video_count=Count("videos")
        )
        course_id = self.request.query_params.get("course")
        if course_id:
            qs = qs.filter(course_id=course_id)
        return qs


class InstructorLessonViewSet(viewsets.ModelViewSet):
    """
    Instructor CRUD on lessons.
    /api/v1/lessons/instructor/
    """
    serializer_class = LessonSerializer
    permission_classes = [IsAuthenticated, IsAdminOrInstructor]

    def get_queryset(self):
        user = self.request.user
        qs = Lesson.objects.select_related("course")
        if user.role == "instructor":
            qs = qs.filter(course__instructor=user)
        course_id = self.request.query_params.get("course")
        if course_id:
            qs = qs.filter(course_id=course_id)
        return qs
