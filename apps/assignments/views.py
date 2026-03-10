from django.utils import timezone
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.core.pagination import StandardPagination
from apps.core.permissions import IsAdminOrInstructor, IsStudent
from apps.assignments.models import Assignment, Submission
from apps.assignments.serializers import (
    AssignmentSerializer,
    AssignmentListSerializer,
    GradeSubmissionSerializer,
    SubmissionSerializer,
    SubmitAssignmentSerializer,
)


class InstructorAssignmentViewSet(viewsets.ModelViewSet):
    """
    /api/v1/assignments/instructor/
    Instructor CRUD on assignments + grading.
    """
    serializer_class = AssignmentSerializer
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

    @action(detail=True, methods=["get"])
    def submissions(self, request, pk=None):
        """List all submissions for an assignment."""
        assignment = self.get_object()
        subs = assignment.submissions.select_related("student").all()
        return Response(SubmissionSerializer(subs, many=True).data)

    @action(detail=True, methods=["post"], url_path="grade/(?P<submission_id>[^/.]+)")
    def grade(self, request, pk=None, submission_id=None):
        """Grade a specific submission."""
        assignment = self.get_object()
        try:
            submission = assignment.submissions.get(id=submission_id)
        except Submission.DoesNotExist:
            return Response(
                {"detail": "Submission not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = GradeSubmissionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        if serializer.validated_data["score"] > assignment.max_score:
            return Response(
                {"detail": f"Score cannot exceed {assignment.max_score}."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        submission.score = serializer.validated_data["score"]
        submission.feedback = serializer.validated_data.get("feedback", "")
        submission.status = Submission.Status.GRADED
        submission.graded_by = request.user
        submission.graded_at = timezone.now()
        submission.save()

        return Response(SubmissionSerializer(submission).data)


class StudentAssignmentViewSet(viewsets.ReadOnlyModelViewSet):
    """
    /api/v1/assignments/student/
    Student view + submit assignments.
    """
    serializer_class = AssignmentListSerializer
    permission_classes = [IsAuthenticated, IsStudent]

    def get_queryset(self):
        enrolled_courses = self.request.user.enrollments.filter(
            is_active=True
        ).values_list("course_id", flat=True)
        return Assignment.objects.filter(
            course_id__in=enrolled_courses, is_published=True
        )

    @action(detail=True, methods=["post"])
    def submit(self, request, pk=None):
        """Submit an assignment."""
        assignment = self.get_object()
        serializer = SubmitAssignmentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        submission, created = Submission.objects.get_or_create(
            assignment=assignment,
            student=request.user,
            defaults={
                "submission_text": serializer.validated_data.get("submission_text", ""),
                "file_url": serializer.validated_data.get("file_url", ""),
                "status": Submission.Status.SUBMITTED,
                "submitted_at": timezone.now(),
            },
        )
        if not created:
            if submission.status == Submission.Status.GRADED:
                return Response(
                    {"detail": "Assignment already graded."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            submission.submission_text = serializer.validated_data.get(
                "submission_text", submission.submission_text
            )
            submission.file_url = serializer.validated_data.get(
                "file_url", submission.file_url
            )
            submission.status = Submission.Status.SUBMITTED
            submission.submitted_at = timezone.now()
            submission.save()

        return Response(SubmissionSerializer(submission).data)

    @action(detail=True, methods=["get"], url_path="my-submission")
    def my_submission(self, request, pk=None):
        """Get my submission for an assignment."""
        assignment = self.get_object()
        try:
            submission = Submission.objects.get(
                assignment=assignment, student=request.user
            )
            return Response(SubmissionSerializer(submission).data)
        except Submission.DoesNotExist:
            return Response(
                {"detail": "No submission found."},
                status=status.HTTP_404_NOT_FOUND,
            )
