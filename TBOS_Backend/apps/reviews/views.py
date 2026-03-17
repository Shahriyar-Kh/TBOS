from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, AllowAny

from apps.core.api_docs import (
    AUTH_GUIDE,
    COURSE_PARAM,
    PAGE_PARAM,
    PAGE_SIZE_PARAM,
    ROLE_ACCESS_GUIDE,
    STATUS_PARAM,
    paginated_response,
    standard_error_responses,
    success_response,
)
from apps.core.exceptions import api_success, api_error
from apps.core.mixins import MultiSerializerMixin
from apps.core.pagination import StandardPagination
from apps.core.permissions import IsAdmin, IsStudent, IsInstructor, IsOwnerOrAdmin
from apps.reviews.models import Review, ReviewResponse
from apps.reviews.serializers import (
    AdminReviewModerateSerializer,
    InstructorResponseSerializer,
    ReviewCreateSerializer,
    ReviewDetailSerializer,
    ReviewListSerializer,
    ReviewUpdateSerializer,
)
from apps.reviews.services.review_service import ReviewService


@extend_schema_view(
    list=extend_schema(tags=["Reviews"], summary="List public reviews", parameters=[PAGE_PARAM, PAGE_SIZE_PARAM, COURSE_PARAM], responses={200: paginated_response("PublicReviewListResponse", ReviewDetailSerializer), **standard_error_responses(400, 500)}),
    retrieve=extend_schema(tags=["Reviews"], summary="Get public review details", responses={200: success_response("PublicReviewDetailResponse", ReviewDetailSerializer), **standard_error_responses(404, 500)}),
)
class PublicReviewViewSet(viewsets.ReadOnlyModelViewSet):
    """
    GET /api/v1/reviews/public/
    GET /api/v1/reviews/public/?course={id}
    Public listing of published reviews for a course.
    """

    serializer_class = ReviewDetailSerializer
    permission_classes = [AllowAny]
    pagination_class = StandardPagination

    def get_queryset(self):
        qs = (
            Review.objects.filter(status=Review.Status.PUBLISHED)
            .select_related("student")
            .prefetch_related("instructor_response__instructor")
        )
        course_id = self.request.query_params.get("course")
        if course_id:
            qs = qs.filter(course_id=course_id)
        return qs

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return api_success(data=serializer.data, message="Reviews retrieved.")

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return api_success(data=serializer.data, message="Review details retrieved.")


@extend_schema_view(
    list=extend_schema(tags=["Reviews"], summary="List student reviews", parameters=[PAGE_PARAM, PAGE_SIZE_PARAM], responses={200: paginated_response("StudentReviewListResponse", ReviewListSerializer), **standard_error_responses(401, 403, 500)}),
    retrieve=extend_schema(tags=["Reviews"], summary="Get student review details", responses={200: success_response("StudentReviewDetailResponse", ReviewDetailSerializer), **standard_error_responses(401, 403, 404, 500)}),
    create=extend_schema(tags=["Reviews"], summary="Create review", request=ReviewCreateSerializer, responses={201: success_response("StudentReviewCreateResponse", ReviewDetailSerializer), **standard_error_responses(400, 401, 403, 500)}),
    update=extend_schema(tags=["Reviews"], summary="Update review", request=ReviewUpdateSerializer, responses={200: success_response("StudentReviewUpdateResponse", ReviewDetailSerializer), **standard_error_responses(400, 401, 403, 404, 500)}),
    partial_update=extend_schema(tags=["Reviews"], summary="Partially update review", request=ReviewUpdateSerializer, responses={200: success_response("StudentReviewPartialUpdateResponse", ReviewDetailSerializer), **standard_error_responses(400, 401, 403, 404, 500)}),
    destroy=extend_schema(tags=["Reviews"], summary="Delete review", responses={200: success_response("StudentReviewDeleteResponse", None), **standard_error_responses(401, 403, 404, 500)}),
)
class StudentReviewViewSet(MultiSerializerMixin, viewsets.ModelViewSet):
    """
    POST   /api/v1/reviews/         — Submit review
    PUT    /api/v1/reviews/{id}/     — Edit review
    DELETE /api/v1/reviews/{id}/     — Delete review
    GET    /api/v1/reviews/          — List own reviews
    """

    serializer_classes = {
        "create": ReviewCreateSerializer,
        "update": ReviewUpdateSerializer,
        "partial_update": ReviewUpdateSerializer,
        "default": ReviewDetailSerializer,
    }
    serializer_class = ReviewDetailSerializer
    permission_classes = [IsAuthenticated, IsStudent]
    pagination_class = StandardPagination

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Review.objects.none()
        return (
            Review.objects.filter(student=self.request.user)
            .select_related("student", "course")
            .prefetch_related("instructor_response__instructor")
        )

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = ReviewListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = ReviewListSerializer(queryset, many=True)
        return api_success(data=serializer.data, message="Your reviews retrieved.")

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        review = ReviewService.create_review(
            student=request.user,
            course=data["course"],
            rating=data["rating"],
            review_text=data["review_text"],
        )
        return api_success(
            data=ReviewDetailSerializer(review).data,
            message="Review submitted successfully.",
            status_code=status.HTTP_201_CREATED,
        )

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        if instance.student != request.user:
            return api_error(
                message="You can only edit your own reviews.",
                status_code=status.HTTP_403_FORBIDDEN,
            )
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        review = ReviewService.update_review(
            review=instance,
            rating=serializer.validated_data.get("rating"),
            review_text=serializer.validated_data.get("review_text"),
        )
        return api_success(
            data=ReviewDetailSerializer(review).data,
            message="Review updated successfully.",
        )

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.student != request.user:
            return api_error(
                message="You can only delete your own reviews.",
                status_code=status.HTTP_403_FORBIDDEN,
            )
        ReviewService.delete_review(instance)
        return api_success(
            message="Review deleted successfully.",
            status_code=status.HTTP_200_OK,
        )

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = ReviewDetailSerializer(instance)
        return api_success(data=serializer.data, message="Review details retrieved.")


@extend_schema_view(
    list=extend_schema(tags=["Reviews"], summary="List instructor course reviews", description=f"List reviews on the authenticated instructor courses.\n\n{AUTH_GUIDE}\n\n{ROLE_ACCESS_GUIDE}", parameters=[PAGE_PARAM, PAGE_SIZE_PARAM, COURSE_PARAM], responses={200: paginated_response("InstructorReviewListResponse", ReviewDetailSerializer), **standard_error_responses(401, 403, 500)}),
    respond=extend_schema(tags=["Reviews"], summary="Respond to course review", request=InstructorResponseSerializer, responses={201: success_response("InstructorReviewRespondResponse", ReviewDetailSerializer), **standard_error_responses(400, 401, 403, 404, 500)}),
)
class InstructorReviewViewSet(viewsets.GenericViewSet):
    """
    POST /api/v1/reviews/instructor/respond/ — Respond to a review
    GET  /api/v1/reviews/instructor/         — List reviews for instructor courses
    """

    permission_classes = [IsAuthenticated, IsInstructor]
    pagination_class = StandardPagination

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Review.objects.none()
        return (
            Review.objects.filter(course__instructor=self.request.user)
            .select_related("student", "course")
            .prefetch_related("instructor_response__instructor")
        )

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        course_id = request.query_params.get("course")
        if course_id:
            queryset = queryset.filter(course_id=course_id)
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = ReviewDetailSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = ReviewDetailSerializer(queryset, many=True)
        return api_success(data=serializer.data, message="Course reviews retrieved.")

    @action(detail=False, methods=["post"])
    def respond(self, request):
        serializer = InstructorResponseSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        review_id = serializer.validated_data["review_id"]
        try:
            review = Review.objects.select_related("course").get(id=review_id)
        except Review.DoesNotExist:
            return api_error(
                message="Review not found.",
                status_code=status.HTTP_404_NOT_FOUND,
            )

        # Ensure instructor owns the course
        if review.course.instructor != request.user:
            return api_error(
                message="You can only respond to reviews on your own courses.",
                status_code=status.HTTP_403_FORBIDDEN,
            )

        response_obj = ReviewService.add_instructor_response(
            review=review,
            instructor=request.user,
            response_text=serializer.validated_data["response_text"],
        )
        review.refresh_from_db()
        return api_success(
            data=ReviewDetailSerializer(review).data,
            message="Response added successfully.",
            status_code=status.HTTP_201_CREATED,
        )


@extend_schema_view(
    list=extend_schema(tags=["Reviews"], summary="List all reviews for moderation", parameters=[PAGE_PARAM, PAGE_SIZE_PARAM, STATUS_PARAM, COURSE_PARAM], responses={200: paginated_response("AdminReviewListResponse", ReviewDetailSerializer), **standard_error_responses(401, 403, 500)}),
    moderate=extend_schema(tags=["Reviews"], summary="Moderate review status", request=AdminReviewModerateSerializer, responses={200: success_response("AdminReviewModerateResponse", ReviewDetailSerializer), **standard_error_responses(400, 401, 403, 404, 500)}),
)
class AdminReviewViewSet(viewsets.GenericViewSet):
    """
    GET /api/v1/reviews/admin/             — View all reviews
    PUT /api/v1/reviews/admin/{id}/moderate/ — Approve or reject review
    """

    permission_classes = [IsAuthenticated, IsAdmin]
    pagination_class = StandardPagination

    def get_queryset(self):
        return (
            Review.objects.all()
            .select_related("student", "course")
            .prefetch_related("instructor_response__instructor")
        )

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        status_filter = request.query_params.get("status")
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        course_id = request.query_params.get("course")
        if course_id:
            queryset = queryset.filter(course_id=course_id)
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = ReviewDetailSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = ReviewDetailSerializer(queryset, many=True)
        return api_success(data=serializer.data, message="All reviews retrieved.")

    @action(detail=True, methods=["put"])
    def moderate(self, request, pk=None):
        try:
            review = Review.objects.get(id=pk)
        except Review.DoesNotExist:
            return api_error(
                message="Review not found.",
                status_code=status.HTTP_404_NOT_FOUND,
            )

        serializer = AdminReviewModerateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        old_status = review.status
        review.status = serializer.validated_data["status"]
        review.save(update_fields=["status", "updated_at"])

        # Recalculate course rating when moderation changes published state
        if old_status != review.status:
            ReviewService._refresh_course_rating(review.course)

        return api_success(
            data=ReviewDetailSerializer(review).data,
            message=f"Review status changed to {review.status}.",
        )
