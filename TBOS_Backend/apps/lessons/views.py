import logging

from drf_spectacular.utils import OpenApiExample, extend_schema, extend_schema_view
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from apps.core.api_docs import (
    AUTH_GUIDE,
    COURSE_EXAMPLE,
    LESSON_EXAMPLE,
    PAGE_PARAM,
    PAGE_SIZE_PARAM,
    ROLE_ACCESS_GUIDE,
    COURSE_PARAM,
    SECTION_PARAM,
    paginated_response,
    standard_error_responses,
    success_example,
    success_response,
)
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

@extend_schema_view(
    list=extend_schema(
        tags=["Lessons"],
        summary="List course sections",
        description=f"List sections for instructor-owned courses.\n\n{AUTH_GUIDE}\n\n{ROLE_ACCESS_GUIDE}",
        parameters=[PAGE_PARAM, PAGE_SIZE_PARAM, COURSE_PARAM],
        responses={200: paginated_response("InstructorSectionListResponse", CourseSectionDetailSerializer), **standard_error_responses(401, 403, 500)},
    ),
    retrieve=extend_schema(tags=["Lessons"], summary="Get section details", responses={200: success_response("InstructorSectionDetailResponse", CourseSectionDetailSerializer), **standard_error_responses(401, 403, 404, 500)}),
    create=extend_schema(tags=["Lessons"], summary="Create a course section", request=CourseSectionCreateSerializer, responses={201: success_response("InstructorSectionCreateResponse", CourseSectionDetailSerializer), **standard_error_responses(400, 401, 403, 500)}),
    update=extend_schema(tags=["Lessons"], summary="Update a section", request=CourseSectionUpdateSerializer, responses={200: success_response("InstructorSectionUpdateResponse", CourseSectionDetailSerializer), **standard_error_responses(400, 401, 403, 404, 500)}),
    partial_update=extend_schema(tags=["Lessons"], summary="Partially update a section", request=CourseSectionUpdateSerializer, responses={200: success_response("InstructorSectionPartialUpdateResponse", CourseSectionDetailSerializer), **standard_error_responses(400, 401, 403, 404, 500)}),
    destroy=extend_schema(tags=["Lessons"], summary="Delete a section", responses={200: success_response("InstructorSectionDeleteResponse", None), **standard_error_responses(401, 403, 404, 500)}),
    reorder=extend_schema(
        tags=["Lessons"],
        summary="Reorder course sections",
        description="Bulk reorder sections inside a course.",
        examples=[OpenApiExample("ReorderSections", value={"course_id": "d7637e3d-92f0-4508-bba3-e27863bce58d", "order": [{"id": "f6a4f8d1-c130-49a1-b157-f6c73174f9e3", "order": 1}]}, request_only=True)],
        responses={200: success_response("InstructorSectionReorderResponse", None), **standard_error_responses(400, 401, 403, 500)},
    ),
)
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

@extend_schema_view(
    list=extend_schema(
        tags=["Lessons"],
        summary="List lessons",
        description=f"List lessons under instructor-owned sections.\n\n{AUTH_GUIDE}\n\n{ROLE_ACCESS_GUIDE}",
        parameters=[PAGE_PARAM, PAGE_SIZE_PARAM, SECTION_PARAM],
        responses={200: paginated_response("InstructorLessonListResponse", LessonDetailSerializer), **standard_error_responses(401, 403, 500)},
    ),
    retrieve=extend_schema(tags=["Lessons"], summary="Get lesson details", responses={200: success_response("InstructorLessonDetailResponse", LessonDetailSerializer), **standard_error_responses(401, 403, 404, 500)}),
    create=extend_schema(tags=["Lessons"], summary="Create a lesson", request=LessonCreateSerializer, responses={201: success_response("InstructorLessonCreateResponse", LessonDetailSerializer), **standard_error_responses(400, 401, 403, 500)}),
    update=extend_schema(tags=["Lessons"], summary="Update a lesson", request=LessonUpdateSerializer, responses={200: success_response("InstructorLessonUpdateResponse", LessonDetailSerializer), **standard_error_responses(400, 401, 403, 404, 500)}),
    partial_update=extend_schema(tags=["Lessons"], summary="Partially update a lesson", request=LessonUpdateSerializer, responses={200: success_response("InstructorLessonPartialUpdateResponse", LessonDetailSerializer), **standard_error_responses(400, 401, 403, 404, 500)}),
    destroy=extend_schema(tags=["Lessons"], summary="Delete a lesson", responses={200: success_response("InstructorLessonDeleteResponse", None), **standard_error_responses(401, 403, 404, 500)}),
    reorder=extend_schema(
        tags=["Lessons"],
        summary="Reorder lessons",
        description="Bulk reorder lessons inside a section.",
        examples=[OpenApiExample("ReorderLessons", value={"section_id": "6d3e833f-9a65-4aaf-ab6a-70076b0fa554", "order": [{"id": LESSON_EXAMPLE["id"], "order": 1}]}, request_only=True)],
        responses={200: success_response("InstructorLessonReorderResponse", None), **standard_error_responses(400, 401, 403, 500)},
    ),
)
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

@extend_schema_view(
    retrieve=extend_schema(
        tags=["Lessons"],
        summary="Get public course curriculum",
        description="Return full section and lesson structure for a course by slug.",
        responses={
            200: success_response(
                "CourseCurriculumResponse",
                None,
                examples=[
                    success_example(
                        "CurriculumSuccess",
                        "Curriculum retrieved successfully.",
                        {"course_id": COURSE_EXAMPLE["id"], "title": COURSE_EXAMPLE["title"], "slug": COURSE_EXAMPLE["slug"], "sections": [{"id": "f6a4f8d1-c130-49a1-b157-f6c73174f9e3", "title": "Service Design", "order": 1, "lessons": [LESSON_EXAMPLE]}]},
                    )
                ],
            ),
            **standard_error_responses(404, 500),
        },
    )
)
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

@extend_schema_view(
    list=extend_schema(
        tags=["Lessons"],
        summary="List preview lessons",
        description="Public listing of preview-enabled lessons, optionally filtered by section.",
        parameters=[SECTION_PARAM],
        responses={200: success_response("PublicLessonListResponse", LessonListSerializer, many=True), **standard_error_responses(500)},
    )
)
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

