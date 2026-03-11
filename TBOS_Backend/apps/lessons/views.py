import logging

from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from apps.core.exceptions import api_error, api_success
from apps.core.mixins import APIResponseMixin
from apps.core.pagination import StandardPagination
from apps.core.permissions import IsAdmin, IsOwnerInstructor
from apps.courses.models import Course
from apps.lessons.models import CourseSection, Lesson
from apps.lessons.serializers import (
    CourseCurriculumSerializer,
    CourseSectionCreateSerializer,
    CourseSectionDetailSerializer,
    CourseSectionUpdateSerializer,
    LessonCreateSerializer,
    LessonDetailSerializer,
    LessonListSerializer,
    LessonUpdateSerializer,
)
from apps.lessons.services.lesson_service import LessonService

logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────────────────────
# Instructor: Section management
# ──────────────────────────────────────────────────────────────

class InstructorSectionViewSet(APIResponseMixin, viewsets.ModelViewSet):
    """
    Instructor CRUD on course sections.

    POST   /api/v1/lessons/instructor/sections/           – create section
    GET    /api/v1/lessons/instructor/sections/           – list sections
    GET    /api/v1/lessons/instructor/sections/{id}/      – retrieve section
    PUT    /api/v1/lessons/instructor/sections/{id}/      – update section
    PATCH  /api/v1/lessons/instructor/sections/{id}/      – partial update
    DELETE /api/v1/lessons/instructor/sections/{id}/      – delete section
    POST   /api/v1/lessons/instructor/sections/reorder/   – bulk reorder
    """

    permission_classes = [IsAuthenticated, IsOwnerInstructor]
    pagination_class = StandardPagination

    def get_serializer_class(self):
        if self.action == "create":
            return CourseSectionCreateSerializer
        if self.action in ("update", "partial_update"):
            return CourseSectionUpdateSerializer
        return CourseSectionDetailSerializer

    def get_queryset(self):
        user = self.request.user
        if getattr(self, "swagger_fake_view", False):
            return CourseSection.objects.none()
        qs = CourseSection.objects.select_related("course").prefetch_related("lessons")
        if user.role == "instructor":
            qs = qs.filter(course__instructor=user)
        course_id = self.request.query_params.get("course")
        if course_id:
            qs = qs.filter(course_id=course_id)
        return qs.order_by("order")

    def get_object(self):
        obj = super().get_object()
        self.check_object_permissions(self.request, obj)
        return obj

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            paginated = self.get_paginated_response(serializer.data)
            return api_success(data=paginated.data, message="Sections retrieved successfully.")
        serializer = self.get_serializer(queryset, many=True)
        return api_success(data=serializer.data, message="Sections retrieved successfully.")

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = CourseSectionDetailSerializer(instance)
        return self.success_response(data=serializer.data, message="Section retrieved successfully.")

    def create(self, request, *args, **kwargs):
        serializer = CourseSectionCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        course = serializer.validated_data.get("course")
        self.check_object_permissions(request, course)
        section = LessonService.create_section(
            course=course,
            validated_data=serializer.validated_data,
        )
        out = CourseSectionDetailSerializer(section)
        return self.created_response(data=out.data, message="Section created successfully.")

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = CourseSectionUpdateSerializer(
            instance, data=request.data, partial=partial
        )
        serializer.is_valid(raise_exception=True)
        section = LessonService.update_section(
            section=instance, validated_data=serializer.validated_data
        )
        out = CourseSectionDetailSerializer(section)
        return self.success_response(data=out.data, message="Section updated successfully.")

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        LessonService.delete_section(instance)
        return self.success_response(message="Section deleted successfully.")

    @action(detail=False, methods=["post"], url_path="reorder")
    def reorder(self, request):
        """POST /api/v1/lessons/instructor/sections/reorder/
        Body: {"course_id": "<uuid>", "order": [{"id": "...", "order": 1}, ...]}
        """
        course_id = request.data.get("course_id")
        section_order = request.data.get("order", [])
        if not course_id:
            return api_error(message="course_id is required.", status_code=status.HTTP_400_BAD_REQUEST)
        LessonService.reorder_sections(course_id=course_id, section_order=section_order)
        return self.success_response(message="Sections reordered successfully.")


# ──────────────────────────────────────────────────────────────
# Instructor: Lesson management
# ──────────────────────────────────────────────────────────────

class InstructorLessonViewSet(APIResponseMixin, viewsets.ModelViewSet):
    """
    Instructor CRUD on lessons.

    POST   /api/v1/lessons/instructor/lessons/           – create lesson
    GET    /api/v1/lessons/instructor/lessons/           – list lessons
    GET    /api/v1/lessons/instructor/lessons/{id}/      – retrieve lesson
    PUT    /api/v1/lessons/instructor/lessons/{id}/      – update lesson
    PATCH  /api/v1/lessons/instructor/lessons/{id}/      – partial update
    DELETE /api/v1/lessons/instructor/lessons/{id}/      – delete lesson
    POST   /api/v1/lessons/instructor/lessons/reorder/   – bulk reorder
    """

    permission_classes = [IsAuthenticated, IsOwnerInstructor]
    pagination_class = StandardPagination

    def get_serializer_class(self):
        if self.action == "create":
            return LessonCreateSerializer
        if self.action in ("update", "partial_update"):
            return LessonUpdateSerializer
        return LessonDetailSerializer

    def get_queryset(self):
        user = self.request.user
        if getattr(self, "swagger_fake_view", False):
            return Lesson.objects.none()
        qs = Lesson.objects.select_related("section__course")
        if user.role == "instructor":
            qs = qs.filter(section__course__instructor=user)
        section_id = self.request.query_params.get("section")
        if section_id:
            qs = qs.filter(section_id=section_id)
        return qs.order_by("order")

    def get_object(self):
        obj = super().get_object()
        self.check_object_permissions(self.request, obj)
        return obj

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            paginated = self.get_paginated_response(serializer.data)
            return api_success(data=paginated.data, message="Lessons retrieved successfully.")
        serializer = self.get_serializer(queryset, many=True)
        return api_success(data=serializer.data, message="Lessons retrieved successfully.")

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = LessonDetailSerializer(instance)
        return self.success_response(data=serializer.data, message="Lesson retrieved successfully.")

    def create(self, request, *args, **kwargs):
        serializer = LessonCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        section = serializer.validated_data.get("section")
        self.check_object_permissions(request, section)
        lesson = LessonService.create_lesson(
            section=section,
            validated_data=serializer.validated_data,
        )
        out = LessonDetailSerializer(lesson)
        return self.created_response(data=out.data, message="Lesson created successfully.")

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = LessonUpdateSerializer(
            instance, data=request.data, partial=partial
        )
        serializer.is_valid(raise_exception=True)
        lesson = LessonService.update_lesson(
            lesson=instance, validated_data=serializer.validated_data
        )
        out = LessonDetailSerializer(lesson)
        return self.success_response(data=out.data, message="Lesson updated successfully.")

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        LessonService.delete_lesson(instance)
        return self.success_response(message="Lesson deleted successfully.")

    @action(detail=False, methods=["post"], url_path="reorder")
    def reorder(self, request):
        """POST /api/v1/lessons/instructor/lessons/reorder/
        Body: {"section_id": "<uuid>", "order": [{"id": "...", "order": 1}, ...]}
        """
        section_id = request.data.get("section_id")
        lesson_order = request.data.get("order", [])
        if not section_id:
            return api_error(message="section_id is required.", status_code=status.HTTP_400_BAD_REQUEST)
        LessonService.reorder_lessons(section_id=section_id, lesson_order=lesson_order)
        return self.success_response(message="Lessons reordered successfully.")


# ──────────────────────────────────────────────────────────────
# Public curriculum endpoint
# ──────────────────────────────────────────────────────────────

class CourseCurriculumView(viewsets.ViewSet):
    """
    GET /api/v1/courses/{slug}/curriculum/
    Returns the full structured curriculum for a course.
    Preview lessons are visible to everyone; non-preview lessons
    require authentication (checked by the client / enrollment logic).
    """

    permission_classes = [AllowAny]

    def retrieve(self, request, slug=None):
        try:
            course = LessonService.get_course_curriculum(slug=slug)
        except Course.DoesNotExist:
            return api_error(message="Course not found.", status_code=status.HTTP_404_NOT_FOUND)

        data = {
            "course_id": str(course.id),
            "title": course.title,
            "slug": course.slug,
            "sections": CourseSectionDetailSerializer(
                course.sections.order_by("order").prefetch_related("lessons"),
                many=True,
            ).data,
        }
        return api_success(data=data, message="Curriculum retrieved successfully.")


# ──────────────────────────────────────────────────────────────
# Public lesson listing (legacy)
# ──────────────────────────────────────────────────────────────

class PublicLessonListView(viewsets.ReadOnlyModelViewSet):
    """
    GET /api/v1/lessons/public/?section={section_id}
    Public read-only listing of preview lessons for a section.
    """

    serializer_class = LessonListSerializer
    permission_classes = [AllowAny]
    pagination_class = None

    def get_queryset(self):
        qs = Lesson.objects.filter(is_preview=True).select_related("section")
        section_id = self.request.query_params.get("section")
        if section_id:
            qs = qs.filter(section_id=section_id)
        return qs

