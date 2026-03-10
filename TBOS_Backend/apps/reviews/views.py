from django.db.models import Avg
from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response

from apps.core.pagination import StandardPagination
from apps.core.permissions import IsStudent, IsOwnerOrAdmin
from apps.reviews.models import Review
from apps.reviews.serializers import ReviewCreateSerializer, ReviewSerializer


class PublicReviewViewSet(viewsets.ReadOnlyModelViewSet):
    """
    GET /api/v1/reviews/?course={id}
    Public listing of reviews for a course.
    """
    serializer_class = ReviewSerializer
    permission_classes = [AllowAny]
    pagination_class = StandardPagination

    def get_queryset(self):
        qs = Review.objects.select_related("student")
        course_id = self.request.query_params.get("course")
        if course_id:
            qs = qs.filter(course_id=course_id)
        return qs


class StudentReviewViewSet(viewsets.ModelViewSet):
    """
    /api/v1/reviews/student/
    Students can create, update, delete their own reviews.
    """
    permission_classes = [IsAuthenticated, IsStudent]

    def get_serializer_class(self):
        if self.action in ("create",):
            return ReviewCreateSerializer
        return ReviewSerializer

    def get_queryset(self):
        return Review.objects.filter(student=self.request.user)

    def perform_create(self, serializer):
        review = serializer.save(student=self.request.user)
        self._update_course_rating(review.course)

    def perform_update(self, serializer):
        review = serializer.save()
        self._update_course_rating(review.course)

    def perform_destroy(self, instance):
        course = instance.course
        instance.delete()
        self._update_course_rating(course)

    @staticmethod
    def _update_course_rating(course):
        avg = course.reviews.aggregate(avg=Avg("rating"))["avg"] or 0
        course.average_rating = round(avg, 2)
        course.save(update_fields=["average_rating"])
