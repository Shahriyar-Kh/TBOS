import logging

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, generics, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from apps.core.exceptions import api_error, api_success
from apps.core.mixins import APIResponseMixin
from apps.core.pagination import StandardPagination
from apps.core.permissions import IsAdmin, IsAdminOrInstructor, IsOwnerInstructor
from apps.courses.models import Category, Course, Language, Level
from apps.courses.serializers import (
    CategorySerializer,
    CourseCreateSerializer,
    CourseDetailSerializer,
    CourseListSerializer,
    CoursePublicSerializer,
    CourseUpdateSerializer,
    LanguageSerializer,
    LevelSerializer,
)
from apps.courses.services.course_service import CourseService

logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────────────────────
# Public / unauthenticated endpoints
# ──────────────────────────────────────────────────────────────

class PublicCourseListView(generics.ListAPIView):
    """
    GET /api/v1/courses/
    Browse all published courses with search, filtering, and sorting.
    """

    serializer_class = CourseListSerializer
    permission_classes = [AllowAny]
    pagination_class = StandardPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = {
        "category__slug": ["exact"],
        "level__id": ["exact"],
        "language__id": ["exact"],
        "is_free": ["exact"],
        "price": ["lte", "gte"],
    }
    search_fields = ["title", "subtitle", "description"]
    ordering_fields = [
        "created_at",
        "price",
        "average_rating",
        "total_enrollments",
    ]
    ordering = ["-created_at"]

    def get_queryset(self):
        return CourseService.list_public_courses()

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            paginated = self.get_paginated_response(serializer.data)
            return api_success(
                data=paginated.data,
                message="Courses retrieved successfully.",
            )
        serializer = self.get_serializer(queryset, many=True)
        return api_success(
            data=serializer.data,
            message="Courses retrieved successfully.",
        )


class PublicCourseDetailView(generics.RetrieveAPIView):
    """
    GET /api/v1/courses/{slug}/
    Return full public details for a single published course.
    """

    serializer_class = CoursePublicSerializer
    permission_classes = [AllowAny]
    lookup_field = "slug"

    def get_queryset(self):
        return (
            Course.objects.filter(status=Course.Status.PUBLISHED)
            .select_related("category", "level", "language", "instructor")
            .prefetch_related("learning_outcomes", "requirements")
        )

    def retrieve(self, request, *args, **kwargs):
        try:
            instance = CourseService.get_course_by_slug(kwargs["slug"])
        except Course.DoesNotExist:
            return api_error(message="Course not found.", status_code=status.HTTP_404_NOT_FOUND)
        serializer = self.get_serializer(instance)
        return api_success(data=serializer.data, message="Course retrieved successfully.")


class CategoryListView(generics.ListAPIView):
    """GET /api/v1/courses/categories/"""

    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [AllowAny]
    pagination_class = None


class LevelListView(generics.ListAPIView):
    """GET /api/v1/courses/levels/"""

    queryset = Level.objects.all()
    serializer_class = LevelSerializer
    permission_classes = [AllowAny]
    pagination_class = None


class LanguageListView(generics.ListAPIView):
    """GET /api/v1/courses/languages/"""

    queryset = Language.objects.all()
    serializer_class = LanguageSerializer
    permission_classes = [AllowAny]
    pagination_class = None


# ──────────────────────────────────────────────────────────────
# Instructor endpoints
# ──────────────────────────────────────────────────────────────

class InstructorCourseViewSet(APIResponseMixin, viewsets.ModelViewSet):
    """
    Instructor CRUD on own courses.

    Endpoints:
      GET    /api/v1/courses/instructor/courses/           – list own courses
      POST   /api/v1/courses/instructor/courses/           – create course
      GET    /api/v1/courses/instructor/courses/{id}/      – retrieve course
      PUT    /api/v1/courses/instructor/courses/{id}/      – update course
      PATCH  /api/v1/courses/instructor/courses/{id}/      – partial update
      POST   /api/v1/courses/instructor/courses/{id}/publish/   – publish
      POST   /api/v1/courses/instructor/courses/{id}/archive/   – archive
    """

    permission_classes = [IsAuthenticated, IsOwnerInstructor]
    pagination_class = StandardPagination

    def get_serializer_class(self):
        if self.action == "create":
            return CourseCreateSerializer
        if self.action in ("update", "partial_update"):
            return CourseUpdateSerializer
        if self.action == "retrieve":
            return CourseDetailSerializer
        return CourseListSerializer

    def get_queryset(self):
        user = self.request.user
        if getattr(self, "swagger_fake_view", False):
            return Course.objects.none()
        if user.role == "admin":
            return Course.objects.select_related(
                "category", "level", "language", "instructor"
            ).all()
        return CourseService.get_instructor_courses(user)

    def get_object(self):
        obj = super().get_object()
        self.check_object_permissions(self.request, obj)
        return obj

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        # Map *_id write-only fields properly
        course = CourseService.create_course(instructor=request.user, validated_data=data)
        out = CourseDetailSerializer(course, context={"request": request})
        return self.created_response(
            data=out.data, message="Course created successfully."
        )

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        course = CourseService.update_course(
            course=instance, validated_data=serializer.validated_data
        )
        out = CourseDetailSerializer(course, context={"request": request})
        return self.success_response(data=out.data, message="Course updated successfully.")

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            paginated = self.get_paginated_response(serializer.data)
            return api_success(
                data=paginated.data,
                message="Courses retrieved successfully.",
            )
        serializer = self.get_serializer(queryset, many=True)
        return api_success(
            data=serializer.data, message="Courses retrieved successfully."
        )

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = CourseDetailSerializer(instance, context={"request": request})
        return self.success_response(
            data=serializer.data, message="Course retrieved successfully."
        )

    @action(detail=True, methods=["post"], url_path="publish")
    def publish(self, request, pk=None):
        """POST /api/v1/courses/instructor/courses/{id}/publish/"""
        course = self.get_object()
        updated = CourseService.publish_course(course=course, user=request.user)
        out = CourseDetailSerializer(updated, context={"request": request})
        return self.success_response(data=out.data, message="Course published successfully.")

    @action(detail=True, methods=["post"], url_path="archive")
    def archive(self, request, pk=None):
        """POST /api/v1/courses/instructor/courses/{id}/archive/"""
        course = self.get_object()
        updated = CourseService.archive_course(course=course, user=request.user)
        out = CourseDetailSerializer(updated, context={"request": request})
        return self.success_response(data=out.data, message="Course archived successfully.")


# ──────────────────────────────────────────────────────────────
# Admin endpoints
# ──────────────────────────────────────────────────────────────

class AdminCourseViewSet(APIResponseMixin, viewsets.ModelViewSet):
    """
    Admin management of all courses.

    Endpoints:
      GET    /api/v1/courses/admin/courses/           – list all courses
      GET    /api/v1/courses/admin/courses/{id}/      – retrieve course
      PUT    /api/v1/courses/admin/courses/{id}/      – update course
      DELETE /api/v1/courses/admin/courses/{id}/      – delete course
      PUT    /api/v1/courses/admin/courses/{id}/publish/ – publish any course
    """

    permission_classes = [IsAuthenticated, IsAdmin]
    pagination_class = StandardPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["status", "category__slug", "level__id", "language__id"]
    search_fields = ["title", "subtitle", "instructor__email"]
    ordering_fields = ["created_at", "price", "average_rating", "total_enrollments"]

    def get_serializer_class(self):
        if self.action in ("update", "partial_update"):
            return CourseUpdateSerializer
        if self.action == "retrieve":
            return CourseDetailSerializer
        return CourseListSerializer

    def get_queryset(self):
        return (
            Course.objects.select_related(
                "category", "level", "language", "instructor"
            )
            .prefetch_related("learning_outcomes", "requirements")
            .order_by("-created_at")
        )

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            paginated = self.get_paginated_response(serializer.data)
            return api_success(
                data=paginated.data, message="Courses retrieved successfully."
            )
        serializer = self.get_serializer(queryset, many=True)
        return api_success(
            data=serializer.data, message="Courses retrieved successfully."
        )

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = CourseDetailSerializer(instance, context={"request": request})
        return self.success_response(
            data=serializer.data, message="Course retrieved successfully."
        )

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        course = CourseService.update_course(
            course=instance, validated_data=serializer.validated_data
        )
        out = CourseDetailSerializer(course, context={"request": request})
        return self.success_response(data=out.data, message="Course updated successfully.")

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.delete()
        return self.success_response(message="Course deleted successfully.")

    @action(detail=True, methods=["put", "post"], url_path="publish")
    def publish(self, request, pk=None):
        """PUT /api/v1/courses/admin/courses/{id}/publish/"""
        course = self.get_object()
        updated = CourseService.publish_course(course=course, user=request.user)
        out = CourseDetailSerializer(updated, context={"request": request})
        return self.success_response(data=out.data, message="Course published successfully.")


class AdminCategoryViewSet(viewsets.ModelViewSet):
    """Admin CRUD for categories."""

    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticated, IsAdmin]


class AdminLevelViewSet(viewsets.ModelViewSet):
    queryset = Level.objects.all()
    serializer_class = LevelSerializer
    permission_classes = [IsAuthenticated, IsAdmin]


class AdminLanguageViewSet(viewsets.ModelViewSet):
    queryset = Language.objects.all()
    serializer_class = LanguageSerializer
    permission_classes = [IsAuthenticated, IsAdmin]
