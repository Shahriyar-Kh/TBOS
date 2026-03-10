from rest_framework import viewsets, generics, status, filters
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend

from apps.core.pagination import StandardPagination
from apps.core.permissions import IsAdmin, IsAdminOrInstructor, IsOwnerOrAdmin
from apps.courses.models import Category, Course, Language, Level
from apps.courses.serializers import (
    CategorySerializer,
    CourseCreateUpdateSerializer,
    CourseDetailSerializer,
    CourseListSerializer,
    LanguageSerializer,
    LevelSerializer,
)


# ──────────────────────────────────────────────
# Public / student endpoints
# ──────────────────────────────────────────────
class PublicCourseListView(generics.ListAPIView):
    """GET /api/v1/courses/ — browse published courses."""
    serializer_class = CourseListSerializer
    permission_classes = [AllowAny]
    pagination_class = StandardPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["category__slug", "level__id", "language__id", "is_free"]
    search_fields = ["title", "subtitle", "description"]
    ordering_fields = ["created_at", "price", "average_rating", "total_enrollments"]

    def get_queryset(self):
        return (
            Course.objects.filter(status=Course.Status.PUBLISHED)
            .select_related("category", "level", "instructor")
            .only(
                "id", "title", "slug", "subtitle", "featured_image",
                "price", "discount", "is_free", "status",
                "average_rating", "total_enrollments", "duration_hours",
                "total_lessons", "created_at",
                "category__id", "category__name", "category__icon", "category__slug",
                "level__id", "level__name",
                "instructor__id", "instructor__first_name", "instructor__last_name",
            )
        )


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


# ──────────────────────────────────────────────
# Instructor endpoints
# ──────────────────────────────────────────────
class InstructorCourseViewSet(viewsets.ModelViewSet):
    """
    Instructor CRUD on own courses.
    /api/v1/courses/instructor/courses/
    """
    permission_classes = [IsAuthenticated, IsAdminOrInstructor]
    pagination_class = StandardPagination

    def get_serializer_class(self):
        if self.action in ("create", "update", "partial_update"):
            return CourseCreateUpdateSerializer
        if self.action == "retrieve":
            return CourseDetailSerializer
        return CourseListSerializer

    def get_queryset(self):
        user = self.request.user
        qs = Course.objects.select_related("category", "level", "language", "instructor")
        if user.role == "instructor":
            qs = qs.filter(instructor=user)
        return qs


# ──────────────────────────────────────────────
# Admin endpoints
# ──────────────────────────────────────────────
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
