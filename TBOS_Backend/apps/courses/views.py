from django.shortcuts import get_object_or_404
from rest_framework import viewsets, generics, status, filters
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend

from apps.core.exceptions import api_success, api_error
from apps.core.pagination import StandardPagination
from apps.core.permissions import IsAdmin, IsAdminOrInstructor, IsOwnerOrAdmin, IsOwnerInstructor
from apps.courses.models import Category, Course, Language, Level
from apps.courses.serializers import (
    CategorySerializer,
    CourseCreateSerializer,
    CourseUpdateSerializer,
    CourseDetailSerializer,
    CourseListSerializer,
    CoursePublicSerializer,
    LanguageSerializer,
    LevelSerializer,
)
from apps.courses.services.course_service import CourseService, CoursePublishError


# ──────────────────────────────────────────────
# Public / student endpoints
# ──────────────────────────────────────────────
class PublicCourseListView(generics.ListAPIView):
    """GET /api/v1/courses/ — browse published courses."""
    serializer_class = CoursePublicSerializer
    permission_classes = [AllowAny]
    pagination_class = StandardPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["category__slug", "level__id", "language__id", "is_free"]
    search_fields = ["title", "subtitle", "description"]
    ordering_fields = ["created_at", "price", "average_rating", "total_enrollments"]
    ordering = ["-created_at"]

    def get_queryset(self):
        return (
            Course.objects.filter(status=Course.Status.PUBLISHED)
            .select_related("category", "level", "language", "instructor")
            .only(
                "id", "title", "slug", "subtitle", "featured_image",
                "price", "discount", "is_free", "status",
                "certificate_available", "average_rating", "rating_count",
                "total_enrollments", "duration_hours", "total_lessons",
                "published_at", "created_at",
                "category__id", "category__name", "category__icon", "category__slug",
                "level__id", "level__name",
                "language__id", "language__name",
                "instructor__id", "instructor__first_name", "instructor__last_name",
            )
        )

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            paginated = self.get_paginated_response(serializer.data)
            return api_success(data=paginated.data, message="Courses retrieved successfully.")
        serializer = self.get_serializer(queryset, many=True)
        return api_success(data=serializer.data, message="Courses retrieved successfully.")


class PublicCourseDetailView(generics.RetrieveAPIView):
    """GET /api/v1/courses/{slug}/ — course detail by slug."""
    serializer_class = CourseDetailSerializer
    permission_classes = [AllowAny]
    lookup_field = "slug"

    def get_queryset(self):
        return (
            Course.objects.filter(status=Course.Status.PUBLISHED)
            .select_related("category", "level", "language", "instructor")
            .prefetch_related("learning_outcomes", "requirements")
        )

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return api_success(data=serializer.data, message="Course retrieved successfully.")


class CategoryListView(generics.ListAPIView):
    """GET /api/v1/courses/categories/"""
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [AllowAny]
    pagination_class = None

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return api_success(data=serializer.data, message="Categories retrieved successfully.")


class LevelListView(generics.ListAPIView):
    """GET /api/v1/courses/levels/"""
    queryset = Level.objects.all()
    serializer_class = LevelSerializer
    permission_classes = [AllowAny]
    pagination_class = None

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return api_success(data=serializer.data, message="Levels retrieved successfully.")


class LanguageListView(generics.ListAPIView):
    """GET /api/v1/courses/languages/"""
    queryset = Language.objects.all()
    serializer_class = LanguageSerializer
    permission_classes = [AllowAny]
    pagination_class = None

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return api_success(data=serializer.data, message="Languages retrieved successfully.")


# ──────────────────────────────────────────────
# Instructor endpoints
# ──────────────────────────────────────────────
class InstructorCourseViewSet(viewsets.ModelViewSet):
    """
    Instructor CRUD on own courses.
    GET    /api/v1/courses/instructor/courses/
    POST   /api/v1/courses/instructor/courses/
    GET    /api/v1/courses/instructor/courses/{id}/
    PUT    /api/v1/courses/instructor/courses/{id}/
    PATCH  /api/v1/courses/instructor/courses/{id}/
    DELETE /api/v1/courses/instructor/courses/{id}/
    POST   /api/v1/courses/instructor/courses/{id}/publish/
    POST   /api/v1/courses/instructor/courses/{id}/archive/
    """
    permission_classes = [IsAuthenticated, IsAdminOrInstructor]
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
        qs = (
            Course.objects.select_related("category", "level", "language", "instructor")
            .order_by("-created_at")
        )
        if user.role == "instructor":
            qs = qs.filter(instructor=user)
        return qs

    def get_object(self):
        obj = get_object_or_404(self.get_queryset(), pk=self.kwargs["pk"])
        self.check_object_permissions(self.request, obj)
        return obj

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        course = CourseService.create_course(request.user, serializer.validated_data)
        out = CourseDetailSerializer(course, context={"request": request})
        return api_success(
            data=out.data,
            message="Course created successfully.",
            status_code=status.HTTP_201_CREATED,
        )

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        course = CourseService.update_course(instance, serializer.validated_data)
        out = CourseDetailSerializer(course, context={"request": request})
        return api_success(data=out.data, message="Course updated successfully.")

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            paginated = self.get_paginated_response(serializer.data)
            return api_success(data=paginated.data, message="Courses retrieved successfully.")
        serializer = self.get_serializer(queryset, many=True)
        return api_success(data=serializer.data, message="Courses retrieved successfully.")

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = CourseDetailSerializer(instance, context={"request": request})
        return api_success(data=serializer.data, message="Course retrieved successfully.")

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.status == Course.Status.PUBLISHED:
            return api_error(
                message="Cannot delete a published course. Archive it first.",
                status_code=status.HTTP_400_BAD_REQUEST,
            )
        instance.delete()
        return api_success(message="Course deleted successfully.", status_code=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=["post"], url_path="publish")
    def publish(self, request, pk=None):
        """POST /api/v1/courses/instructor/courses/{id}/publish/"""
        course = self.get_object()
        try:
            published = CourseService.publish_course(course, request.user)
        except (CoursePublishError, PermissionError) as exc:
            return api_error(message=str(exc), status_code=status.HTTP_400_BAD_REQUEST)
        out = CourseDetailSerializer(published, context={"request": request})
        return api_success(data=out.data, message="Course published successfully.")

    @action(detail=True, methods=["post"], url_path="archive")
    def archive(self, request, pk=None):
        """POST /api/v1/courses/instructor/courses/{id}/archive/"""
        course = self.get_object()
        try:
            archived = CourseService.archive_course(course, request.user)
        except PermissionError as exc:
            return api_error(message=str(exc), status_code=status.HTTP_403_FORBIDDEN)
        out = CourseDetailSerializer(archived, context={"request": request})
        return api_success(data=out.data, message="Course archived successfully.")


# ──────────────────────────────────────────────
# Admin endpoints
# ──────────────────────────────────────────────
class AdminCourseViewSet(viewsets.ModelViewSet):
    """
    Admin management of all courses.
    GET    /api/v1/courses/admin/courses/
    GET    /api/v1/courses/admin/courses/{id}/
    PUT    /api/v1/courses/admin/courses/{id}/
    DELETE /api/v1/courses/admin/courses/{id}/
    POST   /api/v1/courses/admin/courses/{id}/publish/
    POST   /api/v1/courses/admin/courses/{id}/archive/
    """
    permission_classes = [IsAuthenticated, IsAdmin]
    pagination_class = StandardPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["status", "category__slug", "level__id", "language__id", "is_free"]
    search_fields = ["title", "subtitle", "instructor__email"]
    ordering_fields = ["created_at", "price", "average_rating", "total_enrollments", "status"]
    ordering = ["-created_at"]

    def get_queryset(self):
        return (
            Course.objects.all()
            .select_related("category", "level", "language", "instructor")
        )

    def get_serializer_class(self):
        if self.action in ("update", "partial_update"):
            return CourseUpdateSerializer
        if self.action == "retrieve":
            return CourseDetailSerializer
        return CourseListSerializer

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            paginated = self.get_paginated_response(serializer.data)
            return api_success(data=paginated.data, message="All courses retrieved successfully.")
        serializer = self.get_serializer(queryset, many=True)
        return api_success(data=serializer.data, message="All courses retrieved successfully.")

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = CourseDetailSerializer(instance, context={"request": request})
        return api_success(data=serializer.data, message="Course retrieved successfully.")

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        course = CourseService.update_course(instance, serializer.validated_data)
        out = CourseDetailSerializer(course, context={"request": request})
        return api_success(data=out.data, message="Course updated successfully.")

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.delete()
        return api_success(message="Course deleted successfully.", status_code=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=["post"], url_path="publish")
    def publish(self, request, pk=None):
        """POST /api/v1/courses/admin/courses/{id}/publish/"""
        course = self.get_object()
        try:
            published = CourseService.publish_course(course, request.user)
        except CoursePublishError as exc:
            return api_error(message=str(exc), status_code=status.HTTP_400_BAD_REQUEST)
        out = CourseDetailSerializer(published, context={"request": request})
        return api_success(data=out.data, message="Course published successfully.")

    @action(detail=True, methods=["post"], url_path="archive")
    def archive(self, request, pk=None):
        """POST /api/v1/courses/admin/courses/{id}/archive/"""
        course = self.get_object()
        try:
            archived = CourseService.archive_course(course, request.user)
        except PermissionError as exc:
            return api_error(message=str(exc), status_code=status.HTTP_403_FORBIDDEN)
        out = CourseDetailSerializer(archived, context={"request": request})
        return api_success(data=out.data, message="Course archived successfully.")


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
