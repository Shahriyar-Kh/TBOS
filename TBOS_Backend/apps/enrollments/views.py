from drf_spectacular.utils import OpenApiExample, extend_schema, extend_schema_view
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated

from apps.core.api_docs import (
    AUTH_GUIDE,
    COURSE_PARAM,
    PAGE_PARAM,
    PAGE_SIZE_PARAM,
    ROLE_ACCESS_GUIDE,
    STATUS_PARAM,
    STUDENT_PARAM,
    paginated_response,
    standard_error_responses,
    success_example,
    success_response,
)
from apps.core.exceptions import api_success, api_error
from apps.core.pagination import StandardPagination
from apps.core.permissions import IsStudent, IsAdmin, IsAdminOrInstructor
from apps.courses.models import Course
from apps.enrollments.models import Enrollment, LessonProgress
from apps.enrollments.serializers import (
    EnrollmentCreateSerializer,
    EnrollmentDetailSerializer,
    EnrollmentSerializer,
    LessonProgressSerializer,
    MarkLessonCompleteSerializer,
    VideoProgressSerializer,
    VideoProgressUpdateSerializer,
)
from apps.enrollments.services.enrollment_service import EnrollmentService
from apps.lessons.models import Lesson
from apps.videos.models import Video


# ──────────────────────────────────────────────
# Student endpoints
# ──────────────────────────────────────────────

@extend_schema_view(
    list=extend_schema(
        tags=["Enrollments"],
        summary="List student enrollments",
        description=f"Return current student enrollments with progress metadata.\n\n{AUTH_GUIDE}",
        parameters=[PAGE_PARAM, PAGE_SIZE_PARAM],
        responses={200: paginated_response("StudentEnrollmentListResponse", EnrollmentSerializer), **standard_error_responses(401, 403, 500)},
    ),
    retrieve=extend_schema(tags=["Enrollments"], summary="Get enrollment details", responses={200: success_response("StudentEnrollmentDetailResponse", EnrollmentSerializer), **standard_error_responses(401, 403, 404, 500)}),
    enroll=extend_schema(
        tags=["Enrollments"],
        summary="Enroll in a course",
        request=EnrollmentCreateSerializer,
        responses={201: success_response("StudentEnrollResponse", EnrollmentSerializer), **standard_error_responses(400, 401, 403, 404, 500)},
    ),
    progress=extend_schema(tags=["Enrollments"], summary="Get course progress", responses={200: success_response("EnrollmentProgressResponse", None), **standard_error_responses(401, 403, 404, 500)}),
    complete_lesson=extend_schema(tags=["Enrollments"], summary="Mark lesson complete", request=MarkLessonCompleteSerializer, responses={200: success_response("CompleteLessonResponse", EnrollmentSerializer), **standard_error_responses(400, 401, 403, 404, 500)}),
    video_progress=extend_schema(
        tags=["Enrollments"],
        summary="Update video watch progress",
        request=VideoProgressUpdateSerializer,
        examples=[OpenApiExample("VideoProgress", value={"video_id": "f3d8b6c2-d8f8-4ef0-a2f4-7cbd72b309d4", "watch_time_seconds": 320, "last_position_seconds": 145}, request_only=True)],
        responses={200: success_response("VideoProgressResponse", VideoProgressSerializer), **standard_error_responses(400, 401, 403, 404, 500)},
    ),
)
class StudentEnrollmentViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Student enrollment endpoints.

    GET  /enrollments/student/           → my-courses (list)
    POST /enrollments/student/enroll/    → enroll in a course
    GET  /enrollments/student/{id}/progress/       → lesson progress
    POST /enrollments/student/{id}/complete-lesson/ → mark lesson done
    POST /enrollments/student/video-progress/       → update video position
    """

    serializer_class = EnrollmentSerializer
    permission_classes = [IsAuthenticated, IsStudent]
    pagination_class = StandardPagination

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Enrollment.objects.none()
        return EnrollmentService.get_student_enrollments(self.request.user)

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            paginated = self.get_paginated_response(serializer.data)
            return api_success(data=paginated.data, message="Enrollments retrieved.")
        serializer = self.get_serializer(queryset, many=True)
        return api_success(data=serializer.data, message="Enrollments retrieved.")

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return api_success(data=serializer.data, message="Enrollment retrieved.")

    # ── POST /enrollments/student/enroll/ ──
    @action(detail=False, methods=["post"])
    def enroll(self, request):
        serializer = EnrollmentCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            course = Course.objects.get(
                id=serializer.validated_data["course_id"],
                status=Course.Status.PUBLISHED,
            )
        except Course.DoesNotExist:
            return api_error(
                errors={"course_id": "Course not found or not published."},
                message="Course not found or not published.",
                status_code=status.HTTP_404_NOT_FOUND,
            )

        try:
            enrollment = EnrollmentService.enroll_student(request.user, course)
        except ValueError as exc:
            return api_error(
                errors={"detail": str(exc)},
                message=str(exc),
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        return api_success(
            data=EnrollmentSerializer(enrollment).data,
            message="Successfully enrolled in course.",
            status_code=status.HTTP_201_CREATED,
        )

    # ── GET /enrollments/student/{id}/progress/ ──
    @action(detail=True, methods=["get"])
    def progress(self, request, pk=None):
        enrollment = self.get_object()
        progress = enrollment.lesson_progress.select_related("lesson").all()
        return api_success(
            data={
                "enrollment_id": str(enrollment.id),
                "course_title": enrollment.course.title,
                "enrollment_status": enrollment.enrollment_status,
                "progress_percentage": str(enrollment.progress_percentage),
                "completed_lessons_count": enrollment.completed_lessons_count,
                "total_lessons_count": enrollment.total_lessons_count,
                "lessons": LessonProgressSerializer(progress, many=True).data,
            },
            message="Course progress retrieved.",
        )

    # ── POST /enrollments/student/{id}/complete-lesson/ ──
    @action(detail=True, methods=["post"], url_path="complete-lesson")
    def complete_lesson(self, request, pk=None):
        enrollment = self.get_object()
        serializer = MarkLessonCompleteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            lesson = Lesson.objects.get(id=serializer.validated_data["lesson_id"])
        except Lesson.DoesNotExist:
            return api_error(
                errors={"lesson_id": "Lesson not found."},
                message="Lesson not found.",
                status_code=status.HTTP_404_NOT_FOUND,
            )

        try:
            enrollment = EnrollmentService.mark_lesson_completed(enrollment, lesson)
        except ValueError as exc:
            return api_error(
                errors={"detail": str(exc)},
                message=str(exc),
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        return api_success(
            data=EnrollmentSerializer(enrollment).data,
            message="Lesson marked as completed.",
        )

    # ── POST /enrollments/student/video-progress/ ──
    @action(detail=False, methods=["post"], url_path="video-progress")
    def video_progress(self, request):
        serializer = VideoProgressUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            video = Video.objects.select_related("course").get(
                id=serializer.validated_data["video_id"]
            )
        except Video.DoesNotExist:
            return api_error(
                errors={"video_id": "Video not found."},
                message="Video not found.",
                status_code=status.HTTP_404_NOT_FOUND,
            )

        # verify student is enrolled in the video's course
        if not EnrollmentService.check_enrollment_access(request.user, video.course):
            return api_error(
                errors={"detail": "You are not enrolled in this course."},
                message="You are not enrolled in this course.",
                status_code=status.HTTP_403_FORBIDDEN,
            )

        vp = EnrollmentService.update_video_progress(
            student=request.user,
            video=video,
            watch_time_seconds=serializer.validated_data["watch_time_seconds"],
            last_position_seconds=serializer.validated_data["last_position_seconds"],
        )
        return api_success(
            data=VideoProgressSerializer(vp).data,
            message="Video progress updated.",
        )


# ──────────────────────────────────────────────
# Instructor endpoints
# ──────────────────────────────────────────────

@extend_schema_view(
    list=extend_schema(
        tags=["Enrollments"],
        summary="List course enrollments for instructor",
        description=f"Instructor/admin enrollment monitoring endpoint.\n\n{AUTH_GUIDE}\n\n{ROLE_ACCESS_GUIDE}",
        parameters=[PAGE_PARAM, PAGE_SIZE_PARAM, COURSE_PARAM, STUDENT_PARAM],
        responses={200: paginated_response("InstructorEnrollmentListResponse", EnrollmentDetailSerializer), **standard_error_responses(401, 403, 500)},
    ),
    retrieve=extend_schema(tags=["Enrollments"], summary="Get enrollment details for instructor", responses={200: success_response("InstructorEnrollmentDetailResponse", EnrollmentDetailSerializer), **standard_error_responses(401, 403, 404, 500)}),
)
class InstructorEnrollmentViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Instructor enrollment view.

    GET /enrollments/instructor/                  → enrollments in own courses
    GET /enrollments/instructor/?course={id}      → filter by course
    """

    serializer_class = EnrollmentDetailSerializer
    permission_classes = [IsAuthenticated, IsAdminOrInstructor]
    pagination_class = StandardPagination

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Enrollment.objects.none()
        user = self.request.user
        qs = Enrollment.objects.select_related(
            "student", "course__category", "course__level", "course__instructor"
        )
        if user.role == "instructor":
            qs = qs.filter(course__instructor=user)
        course_id = self.request.query_params.get("course")
        if course_id:
            qs = qs.filter(course_id=course_id)
        student_id = self.request.query_params.get("student")
        if student_id:
            qs = qs.filter(student_id=student_id)
        return qs.order_by("-enrolled_at")

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            paginated = self.get_paginated_response(serializer.data)
            return api_success(data=paginated.data, message="Enrollments retrieved.")
        serializer = self.get_serializer(queryset, many=True)
        return api_success(data=serializer.data, message="Enrollments retrieved.")

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return api_success(data=serializer.data, message="Enrollment retrieved.")


# ──────────────────────────────────────────────
# Admin endpoints
# ──────────────────────────────────────────────

@extend_schema_view(
    list=extend_schema(
        tags=["Enrollments"],
        summary="List all enrollments",
        description=f"Administrative enrollment listing with filters.\n\n{AUTH_GUIDE}\n\n{ROLE_ACCESS_GUIDE}",
        parameters=[PAGE_PARAM, PAGE_SIZE_PARAM, COURSE_PARAM, STUDENT_PARAM, STATUS_PARAM],
        responses={200: paginated_response("AdminEnrollmentListResponse", EnrollmentDetailSerializer), **standard_error_responses(401, 403, 500)},
    ),
    retrieve=extend_schema(tags=["Enrollments"], summary="Get enrollment details for admin", responses={200: success_response("AdminEnrollmentDetailResponse", EnrollmentDetailSerializer), **standard_error_responses(401, 403, 404, 500)}),
)
class AdminEnrollmentViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Admin enrollment view — all enrollments.

    GET /enrollments/admin/
    GET /enrollments/admin/?course={id}&student={id}&status={status}
    """

    serializer_class = EnrollmentDetailSerializer
    permission_classes = [IsAuthenticated, IsAdmin]
    pagination_class = StandardPagination

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Enrollment.objects.none()
        qs = Enrollment.objects.select_related(
            "student", "course__category", "course__level", "course__instructor"
        )
        course_id = self.request.query_params.get("course")
        if course_id:
            qs = qs.filter(course_id=course_id)
        student_id = self.request.query_params.get("student")
        if student_id:
            qs = qs.filter(student_id=student_id)
        enrollment_status = self.request.query_params.get("status")
        if enrollment_status:
            qs = qs.filter(enrollment_status=enrollment_status)
        return qs.order_by("-enrolled_at")

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            paginated = self.get_paginated_response(serializer.data)
            return api_success(data=paginated.data, message="Enrollments retrieved.")
        serializer = self.get_serializer(queryset, many=True)
        return api_success(data=serializer.data, message="Enrollments retrieved.")

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return api_success(data=serializer.data, message="Enrollment retrieved.")
