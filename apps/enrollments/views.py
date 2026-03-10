from django.utils import timezone
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.core.pagination import StandardPagination
from apps.core.permissions import IsStudent, IsAdmin, IsAdminOrInstructor
from apps.courses.models import Course
from apps.enrollments.models import Enrollment, LessonProgress
from apps.enrollments.serializers import (
    EnrollmentCreateSerializer,
    EnrollmentSerializer,
    LessonProgressSerializer,
    MarkLessonCompleteSerializer,
)
from apps.lessons.models import Lesson


class StudentEnrollmentViewSet(viewsets.ReadOnlyModelViewSet):
    """
    /api/v1/enrollments/student/
    Students can view their enrollments, enroll in free courses, and track progress.
    """
    serializer_class = EnrollmentSerializer
    permission_classes = [IsAuthenticated, IsStudent]
    pagination_class = StandardPagination

    def get_queryset(self):
        return (
            Enrollment.objects.filter(student=self.request.user)
            .select_related("course__category", "course__level", "course__instructor")
        )

    @action(detail=False, methods=["post"])
    def enroll(self, request):
        """Enroll in a free course."""
        serializer = EnrollmentCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            course = Course.objects.get(
                id=serializer.validated_data["course_id"],
                status=Course.Status.PUBLISHED,
            )
        except Course.DoesNotExist:
            return Response(
                {"detail": "Course not found or not published."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if not course.is_free:
            return Response(
                {"detail": "This course requires payment. Use /api/v1/payments/ instead."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        enrollment, created = Enrollment.objects.get_or_create(
            student=request.user, course=course
        )
        if not created:
            return Response(
                {"detail": "Already enrolled."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        course.total_enrollments += 1
        course.save(update_fields=["total_enrollments"])

        return Response(
            EnrollmentSerializer(enrollment).data,
            status=status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=["get"])
    def progress(self, request, pk=None):
        """Get lesson-by-lesson progress for an enrollment."""
        enrollment = self.get_object()
        progress = enrollment.lesson_progress.select_related("lesson").all()
        return Response(LessonProgressSerializer(progress, many=True).data)

    @action(detail=True, methods=["post"], url_path="complete-lesson")
    def complete_lesson(self, request, pk=None):
        """Mark a lesson as complete."""
        enrollment = self.get_object()
        serializer = MarkLessonCompleteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            lesson = Lesson.objects.get(
                id=serializer.validated_data["lesson_id"],
                course=enrollment.course,
            )
        except Lesson.DoesNotExist:
            return Response(
                {"detail": "Lesson not found in this course."},
                status=status.HTTP_404_NOT_FOUND,
            )

        lp, _ = LessonProgress.objects.get_or_create(
            enrollment=enrollment, lesson=lesson
        )
        lp.is_completed = True
        lp.completed_at = timezone.now()
        lp.save()

        # Update overall progress
        total_lessons = enrollment.course.lessons.count()
        completed = enrollment.lesson_progress.filter(is_completed=True).count()
        enrollment.progress_percent = (
            round(completed / total_lessons * 100, 2) if total_lessons else 0
        )
        enrollment.last_accessed_at = timezone.now()
        if enrollment.progress_percent >= 100:
            enrollment.completed_at = timezone.now()
        enrollment.save()

        return Response(EnrollmentSerializer(enrollment).data)


class AdminEnrollmentViewSet(viewsets.ReadOnlyModelViewSet):
    """
    /api/v1/enrollments/admin/
    Admin view of all enrollments.
    """
    serializer_class = EnrollmentSerializer
    permission_classes = [IsAuthenticated, IsAdmin]
    pagination_class = StandardPagination

    def get_queryset(self):
        qs = Enrollment.objects.select_related(
            "student", "course"
        )
        course_id = self.request.query_params.get("course")
        if course_id:
            qs = qs.filter(course_id=course_id)
        student_id = self.request.query_params.get("student")
        if student_id:
            qs = qs.filter(student_id=student_id)
        return qs


class InstructorEnrollmentViewSet(viewsets.ReadOnlyModelViewSet):
    """
    /api/v1/enrollments/instructor/
    Instructor view of enrollments in their courses.
    """
    serializer_class = EnrollmentSerializer
    permission_classes = [IsAuthenticated, IsAdminOrInstructor]
    pagination_class = StandardPagination

    def get_queryset(self):
        user = self.request.user
        qs = Enrollment.objects.select_related("student", "course")
        if user.role == "instructor":
            qs = qs.filter(course__instructor=user)
        course_id = self.request.query_params.get("course")
        if course_id:
            qs = qs.filter(course_id=course_id)
        return qs
