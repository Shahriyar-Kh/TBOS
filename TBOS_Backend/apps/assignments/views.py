from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated

from apps.core.exceptions import api_success, api_error
from apps.core.mixins import MultiSerializerMixin
from apps.core.pagination import StandardPagination
from apps.core.permissions import IsAdminOrInstructor, IsStudent
from apps.assignments.models import Assignment, AssignmentSubmission
from apps.assignments.serializers import (
    AssignmentCreateSerializer,
    AssignmentGradeSerializer,
    AssignmentListSerializer,
    AssignmentSerializer,
    AssignmentSubmissionSerializer,
    SubmitAssignmentSerializer,
)
from apps.assignments.services.assignment_service import AssignmentService


class InstructorAssignmentViewSet(MultiSerializerMixin, viewsets.ModelViewSet):
    """
    /api/v1/assignments/instructor/
    Instructor CRUD on assignments + grading.
    """

    serializer_class = AssignmentSerializer
    serializer_classes = {
        "list": AssignmentListSerializer,
        "create": AssignmentCreateSerializer,
        "update": AssignmentCreateSerializer,
        "partial_update": AssignmentCreateSerializer,
        "default": AssignmentSerializer,
    }
    permission_classes = [IsAuthenticated, IsAdminOrInstructor]
    pagination_class = StandardPagination

    def get_queryset(self):
        user = self.request.user
        qs = Assignment.objects.select_related("course", "lesson")
        if user.role == "instructor":
            qs = qs.filter(course__instructor=user)
        course_id = self.request.query_params.get("course")
        if course_id:
            qs = qs.filter(course_id=course_id)
        return qs

    def perform_create(self, serializer):
        self._assignment = AssignmentService.create_assignment(serializer.validated_data)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return api_success(
            data=AssignmentSerializer(self._assignment).data,
            message="Assignment created successfully.",
            status_code=status.HTTP_201_CREATED,
        )

    def perform_update(self, serializer):
        self._assignment = AssignmentService.update_assignment(
            self.get_object(), serializer.validated_data
        )

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return api_success(
            data=AssignmentSerializer(self._assignment).data,
            message="Assignment updated successfully.",
        )

    @action(detail=True, methods=["get"])
    def submissions(self, request, pk=None):
        """List all student submissions for an assignment."""
        assignment = self.get_object()
        subs = AssignmentService.get_assignment_submissions(assignment)
        page = self.paginate_queryset(subs)
        if page is not None:
            serializer = AssignmentSubmissionSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        return api_success(
            data=AssignmentSubmissionSerializer(subs, many=True).data,
            message="Submissions retrieved.",
        )

    @action(detail=False, methods=["post"])
    def grade(self, request):
        """Grade a student submission."""
        serializer = AssignmentGradeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        submission_id = serializer.validated_data["submission_id"]
        try:
            submission = (
                AssignmentSubmission.objects
                .select_related("assignment__course")
                .get(id=submission_id)
            )
        except AssignmentSubmission.DoesNotExist:
            return api_error(
                message="Submission not found.",
                status_code=status.HTTP_404_NOT_FOUND,
            )

        # Ensure instructor owns the course (or is admin)
        if request.user.role == "instructor":
            if submission.assignment.course.instructor != request.user:
                return api_error(
                    message="You do not own this course.",
                    status_code=status.HTTP_403_FORBIDDEN,
                )

        try:
            grade = AssignmentService.grade_submission(
                submission=submission,
                score=serializer.validated_data["score"],
                feedback=serializer.validated_data.get("feedback", ""),
                graded_by=request.user,
            )
        except ValueError as e:
            return api_error(message=str(e))

        return api_success(
            data=AssignmentSubmissionSerializer(submission).data,
            message="Submission graded successfully.",
        )


class StudentAssignmentViewSet(viewsets.ReadOnlyModelViewSet):
    """
    /api/v1/assignments/student/
    Student view + submit + view own submissions & results.
    """

    serializer_class = AssignmentListSerializer
    permission_classes = [IsAuthenticated, IsStudent]
    pagination_class = StandardPagination

    def get_queryset(self):
        enrolled_courses = self.request.user.enrollments.filter(
            is_active=True
        ).values_list("course_id", flat=True)
        return Assignment.objects.filter(
            course_id__in=enrolled_courses, is_published=True
        ).select_related("course")

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        return api_success(
            data=AssignmentSerializer(instance).data,
            message="Assignment details retrieved.",
        )

    @action(detail=True, methods=["post"])
    def submit(self, request, pk=None):
        """Submit an assignment."""
        assignment = self.get_object()
        serializer = SubmitAssignmentSerializer(
            data=request.data, context={"assignment": assignment}
        )
        serializer.is_valid(raise_exception=True)

        try:
            submission = AssignmentService.submit_assignment(
                assignment=assignment,
                student=request.user,
                submission_text=serializer.validated_data.get("submission_text", ""),
                file_url=serializer.validated_data.get("file_url", ""),
            )
        except ValueError as e:
            return api_error(message=str(e))

        return api_success(
            data=AssignmentSubmissionSerializer(submission).data,
            message="Assignment submitted successfully.",
            status_code=status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=["get"], url_path="my-submissions")
    def my_submissions(self, request, pk=None):
        """View own submissions for an assignment."""
        assignment = self.get_object()
        subs = AssignmentService.get_student_submissions(assignment, request.user)
        return api_success(
            data=AssignmentSubmissionSerializer(subs, many=True).data,
            message="Your submissions retrieved.",
        )

    @action(detail=True, methods=["get"])
    def result(self, request, pk=None):
        """View grade and feedback for the latest graded submission."""
        assignment = self.get_object()
        submission = (
            AssignmentSubmission.objects
            .filter(
                assignment=assignment,
                student=request.user,
                status=AssignmentSubmission.Status.GRADED,
            )
            .select_related("grade")
            .order_by("-attempt_number")
            .first()
        )
        if not submission:
            return api_error(
                message="No graded submission found.",
                status_code=status.HTTP_404_NOT_FOUND,
            )
        return api_success(
            data=AssignmentSubmissionSerializer(submission).data,
            message="Result retrieved.",
        )
