import logging

from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiExample, OpenApiParameter, extend_schema, extend_schema_view
from rest_framework import filters, generics, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from apps.core.api_docs import (
    AUTH_GUIDE,
    CATEGORY_PARAM,
    COURSE_EXAMPLE,
    LANGUAGE_PARAM,
    LEVEL_PARAM,
    PAGE_PARAM,
    PAGE_SIZE_PARAM,
    ROLE_ACCESS_GUIDE,
    SEARCH_PARAM,
    SORTING_PARAM,
    STATUS_PARAM,
    paginated_response,
    standard_error_responses,
    success_example,
    success_response,
)
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

COURSE_CATEGORY_SLUG_PARAM = OpenApiParameter(
    name="category__slug",
    type=OpenApiTypes.STR,
    location=OpenApiParameter.QUERY,
    description="Filter by category slug.",
)

COURSE_LEVEL_ID_PARAM = OpenApiParameter(
    name="level__id",
    type=OpenApiTypes.UUID,
    location=OpenApiParameter.QUERY,
    description="Filter by course level identifier.",
)

COURSE_LANGUAGE_ID_PARAM = OpenApiParameter(
    name="language__id",
    type=OpenApiTypes.UUID,
    location=OpenApiParameter.QUERY,
    description="Filter by language identifier.",
)

IS_FREE_PARAM = OpenApiParameter(
    name="is_free",
    type=OpenApiTypes.BOOL,
    location=OpenApiParameter.QUERY,
    description="Filter for free or paid courses.",
)

PRICE_LTE_PARAM = OpenApiParameter(
    name="price__lte",
    type=OpenApiTypes.NUMBER,
    location=OpenApiParameter.QUERY,
    description="Filter courses with price less than or equal to the provided value.",
)

PRICE_GTE_PARAM = OpenApiParameter(
    name="price__gte",
    type=OpenApiTypes.NUMBER,
    location=OpenApiParameter.QUERY,
    description="Filter courses with price greater than or equal to the provided value.",
)


# ──────────────────────────────────────────────────────────────
# Public / unauthenticated endpoints
# ──────────────────────────────────────────────────────────────

@extend_schema(
    tags=["Courses"],
    summary="Browse published courses",
    description=(
        "Public course catalog with pagination, keyword search, filtering, and ordering. "
        "Designed for storefront and frontend discovery experiences."
    ),
    parameters=[
        PAGE_PARAM,
        PAGE_SIZE_PARAM,
        SEARCH_PARAM,
        COURSE_CATEGORY_SLUG_PARAM,
        COURSE_LEVEL_ID_PARAM,
        COURSE_LANGUAGE_ID_PARAM,
        IS_FREE_PARAM,
        PRICE_LTE_PARAM,
        PRICE_GTE_PARAM,
        SORTING_PARAM,
    ],
    responses={
        200: paginated_response(
            "PublicCourseListResponse",
            CourseListSerializer,
            description="Published course catalog.",
            examples=[
                success_example(
                    "CourseCatalog",
                    "Courses retrieved successfully.",
                    {
                        "page": 1,
                        "page_size": 20,
                        "total_count": 1,
                        "count": 1,
                        "next": None,
                        "previous": None,
                        "results": [COURSE_EXAMPLE],
                    },
                )
            ],
        ),
        **standard_error_responses(400, 500),
    },
)
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


@extend_schema(
    tags=["Courses"],
    summary="Get public course details",
    description="Return full public metadata for a published course identified by slug.",
    responses={
        200: success_response(
            "PublicCourseDetailResponse",
            CoursePublicSerializer,
            examples=[success_example("CourseDetail", "Course retrieved successfully.", COURSE_EXAMPLE)],
        ),
        **standard_error_responses(404, 500),
    },
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


@extend_schema(
    tags=["Courses"],
    summary="List course categories",
    description="Lookup endpoint used to populate category filters and course creation forms.",
    responses={
        200: success_response("CategoryListResponse", CategorySerializer, many=True),
        **standard_error_responses(500),
    },
)
class CategoryListView(generics.ListAPIView):
    """GET /api/v1/courses/categories/"""

    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [AllowAny]
    pagination_class = None


@extend_schema(
    tags=["Courses"],
    summary="List course levels",
    description="Lookup endpoint used to populate level filters and course authoring forms.",
    responses={
        200: success_response("LevelListResponse", LevelSerializer, many=True),
        **standard_error_responses(500),
    },
)
class LevelListView(generics.ListAPIView):
    """GET /api/v1/courses/levels/"""

    queryset = Level.objects.all()
    serializer_class = LevelSerializer
    permission_classes = [AllowAny]
    pagination_class = None


@extend_schema(
    tags=["Courses"],
    summary="List course languages",
    description="Lookup endpoint used to populate language filters and course authoring forms.",
    responses={
        200: success_response("LanguageListResponse", LanguageSerializer, many=True),
        **standard_error_responses(500),
    },
)
class LanguageListView(generics.ListAPIView):
    """GET /api/v1/courses/languages/"""

    queryset = Language.objects.all()
    serializer_class = LanguageSerializer
    permission_classes = [AllowAny]
    pagination_class = None


# ──────────────────────────────────────────────────────────────
# Instructor endpoints
# ──────────────────────────────────────────────────────────────

@extend_schema_view(
    list=extend_schema(
        tags=["Courses"],
        summary="List instructor-owned courses",
        description=(
            "Return a paginated list of courses owned by the authenticated instructor. "
            "Admins can also use this endpoint to inspect all courses.\n\n"
            f"{AUTH_GUIDE}\n\n{ROLE_ACCESS_GUIDE}"
        ),
        parameters=[PAGE_PARAM, PAGE_SIZE_PARAM],
        responses={
            200: paginated_response("InstructorCourseListResponse", CourseListSerializer),
            **standard_error_responses(401, 403, 500),
        },
    ),
    retrieve=extend_schema(
        tags=["Courses"],
        summary="Get instructor course details",
        description="Return the full editable course resource for an instructor-owned course.",
        responses={
            200: success_response("InstructorCourseDetailResponse", CourseDetailSerializer),
            **standard_error_responses(401, 403, 404, 500),
        },
    ),
    create=extend_schema(
        tags=["Courses"],
        summary="Create a course",
        description="Create a new draft course under the authenticated instructor account.",
        request=CourseCreateSerializer,
        responses={
            201: success_response("InstructorCourseCreateResponse", CourseDetailSerializer),
            **standard_error_responses(400, 401, 403, 500),
        },
        examples=[
            OpenApiExample(
                "CreateCourseRequest",
                value={
                    "title": "Modern Django for Product Teams",
                    "subtitle": "Build and operate production-ready Django services.",
                    "description": "From project setup to observability and deployments.",
                    "thumbnail": "https://res.cloudinary.com/tbos/image/upload/v1/courses/django-thumb.jpg",
                    "promo_video_url": "https://www.youtube.com/watch?v=tbosdemo",
                    "price": "149.00",
                    "discount_price": "99.00",
                    "is_free": False,
                    "certificate_available": True,
                    "category_id": "d7637e3d-92f0-4508-bba3-e27863bce58d",
                    "level_id": "9c935c26-cc6d-49d4-bf63-c71cf6dba11c",
                    "language_id": "00432bf4-6a3f-4b52-9a1c-64db5b0a4adb",
                },
                request_only=True,
            )
        ],
    ),
    update=extend_schema(
        tags=["Courses"],
        summary="Replace a course",
        description="Fully update an existing instructor-owned course.",
        request=CourseUpdateSerializer,
        responses={
            200: success_response("InstructorCourseUpdateResponse", CourseDetailSerializer),
            **standard_error_responses(400, 401, 403, 404, 500),
        },
    ),
    partial_update=extend_schema(
        tags=["Courses"],
        summary="Partially update a course",
        description="Patch selected fields on an instructor-owned course.",
        request=CourseUpdateSerializer,
        responses={
            200: success_response("InstructorCoursePartialUpdateResponse", CourseDetailSerializer),
            **standard_error_responses(400, 401, 403, 404, 500),
        },
    ),
    publish=extend_schema(
        tags=["Courses"],
        summary="Publish a course",
        description="Transition a draft course to the published state after validation is complete.",
        responses={
            200: success_response("InstructorCoursePublishResponse", CourseDetailSerializer),
            **standard_error_responses(401, 403, 404, 500),
        },
    ),
    archive=extend_schema(
        tags=["Courses"],
        summary="Archive a course",
        description="Archive a course so it no longer appears in the public catalog.",
        responses={
            200: success_response("InstructorCourseArchiveResponse", CourseDetailSerializer),
            **standard_error_responses(401, 403, 404, 500),
        },
    ),
)
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

@extend_schema_view(
    list=extend_schema(
        tags=["Courses"],
        summary="List all courses for admin review",
        description=(
            "Administrative course catalog with filtering, search, and ordering for moderation workflows.\n\n"
            f"{AUTH_GUIDE}\n\n{ROLE_ACCESS_GUIDE}"
        ),
        parameters=[
            PAGE_PARAM,
            PAGE_SIZE_PARAM,
            SEARCH_PARAM,
            COURSE_CATEGORY_SLUG_PARAM,
            COURSE_LEVEL_ID_PARAM,
            COURSE_LANGUAGE_ID_PARAM,
            STATUS_PARAM,
            SORTING_PARAM,
        ],
        responses={
            200: paginated_response("AdminCourseListResponse", CourseListSerializer),
            **standard_error_responses(401, 403, 500),
        },
    ),
    retrieve=extend_schema(
        tags=["Courses"],
        summary="Get full course details for admin review",
        responses={
            200: success_response("AdminCourseDetailResponse", CourseDetailSerializer),
            **standard_error_responses(401, 403, 404, 500),
        },
    ),
    update=extend_schema(
        tags=["Courses"],
        summary="Update any course as an admin",
        request=CourseUpdateSerializer,
        responses={
            200: success_response("AdminCourseUpdateResponse", CourseDetailSerializer),
            **standard_error_responses(400, 401, 403, 404, 500),
        },
    ),
    partial_update=extend_schema(
        tags=["Courses"],
        summary="Partially update any course as an admin",
        request=CourseUpdateSerializer,
        responses={
            200: success_response("AdminCoursePartialUpdateResponse", CourseDetailSerializer),
            **standard_error_responses(400, 401, 403, 404, 500),
        },
    ),
    destroy=extend_schema(
        tags=["Courses"],
        summary="Delete a course",
        description="Permanently remove a course and its associated catalog record.",
        responses={
            200: success_response("AdminCourseDeleteResponse", None),
            **standard_error_responses(401, 403, 404, 500),
        },
    ),
    publish=extend_schema(
        tags=["Courses"],
        summary="Force-publish a course",
        description="Administrative publish operation for a course in any state.",
        responses={
            200: success_response("AdminCoursePublishResponse", CourseDetailSerializer),
            **standard_error_responses(401, 403, 404, 500),
        },
    ),
)
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


@extend_schema_view(
    list=extend_schema(tags=["Courses"], summary="List categories", responses={200: success_response("AdminCategoryListResponse", CategorySerializer, many=True)}),
    retrieve=extend_schema(tags=["Courses"], summary="Get category details", responses={200: success_response("AdminCategoryDetailResponse", CategorySerializer), **standard_error_responses(404, 500)}),
    create=extend_schema(tags=["Courses"], summary="Create a category", request=CategorySerializer, responses={201: success_response("AdminCategoryCreateResponse", CategorySerializer), **standard_error_responses(400, 500)}),
    update=extend_schema(tags=["Courses"], summary="Update a category", request=CategorySerializer, responses={200: success_response("AdminCategoryUpdateResponse", CategorySerializer), **standard_error_responses(400, 404, 500)}),
    partial_update=extend_schema(tags=["Courses"], summary="Partially update a category", request=CategorySerializer, responses={200: success_response("AdminCategoryPartialUpdateResponse", CategorySerializer), **standard_error_responses(400, 404, 500)}),
    destroy=extend_schema(tags=["Courses"], summary="Delete a category", responses={204: success_response("AdminCategoryDeleteResponse", None), **standard_error_responses(404, 500)}),
)
class AdminCategoryViewSet(viewsets.ModelViewSet):
    """Admin CRUD for categories."""

    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticated, IsAdmin]


@extend_schema_view(
    list=extend_schema(tags=["Courses"], summary="List levels", responses={200: success_response("AdminLevelListResponse", LevelSerializer, many=True)}),
    retrieve=extend_schema(tags=["Courses"], summary="Get level details", responses={200: success_response("AdminLevelDetailResponse", LevelSerializer), **standard_error_responses(404, 500)}),
    create=extend_schema(tags=["Courses"], summary="Create a level", request=LevelSerializer, responses={201: success_response("AdminLevelCreateResponse", LevelSerializer), **standard_error_responses(400, 500)}),
    update=extend_schema(tags=["Courses"], summary="Update a level", request=LevelSerializer, responses={200: success_response("AdminLevelUpdateResponse", LevelSerializer), **standard_error_responses(400, 404, 500)}),
    partial_update=extend_schema(tags=["Courses"], summary="Partially update a level", request=LevelSerializer, responses={200: success_response("AdminLevelPartialUpdateResponse", LevelSerializer), **standard_error_responses(400, 404, 500)}),
)
class AdminLevelViewSet(viewsets.ModelViewSet):
    queryset = Level.objects.all()
    serializer_class = LevelSerializer
    permission_classes = [IsAuthenticated, IsAdmin]


@extend_schema_view(
    list=extend_schema(tags=["Courses"], summary="List languages", responses={200: success_response("AdminLanguageListResponse", LanguageSerializer, many=True)}),
    retrieve=extend_schema(tags=["Courses"], summary="Get language details", responses={200: success_response("AdminLanguageDetailResponse", LanguageSerializer), **standard_error_responses(404, 500)}),
    create=extend_schema(tags=["Courses"], summary="Create a language", request=LanguageSerializer, responses={201: success_response("AdminLanguageCreateResponse", LanguageSerializer), **standard_error_responses(400, 500)}),
    update=extend_schema(tags=["Courses"], summary="Update a language", request=LanguageSerializer, responses={200: success_response("AdminLanguageUpdateResponse", LanguageSerializer), **standard_error_responses(400, 404, 500)}),
    partial_update=extend_schema(tags=["Courses"], summary="Partially update a language", request=LanguageSerializer, responses={200: success_response("AdminLanguagePartialUpdateResponse", LanguageSerializer), **standard_error_responses(400, 404, 500)}),
)
class AdminLanguageViewSet(viewsets.ModelViewSet):
    queryset = Language.objects.all()
    serializer_class = LanguageSerializer
    permission_classes = [IsAuthenticated, IsAdmin]
