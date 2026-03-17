import pytest

from apps.assignments.models import Assignment
from apps.assignments.serializers import AssignmentCreateSerializer, SubmitAssignmentSerializer
from tests.factories import AssignmentFactory


@pytest.mark.django_db
class TestAssignmentSerializers:
    def test_assignment_create_serializer_rejects_zero_attempts(self):
        assignment = AssignmentFactory(max_attempts=1)
        serializer = AssignmentCreateSerializer(data={
            "course": str(assignment.course_id),
            "lesson": str(assignment.lesson_id),
            "title": assignment.title,
            "description": assignment.description,
            "instructions": assignment.instructions,
            "max_score": assignment.max_score,
            "submission_type": Assignment.SubmissionType.TEXT,
            "max_attempts": 0,
            "is_published": True,
            "order": 1,
        })
        assert not serializer.is_valid()
        assert "max_attempts" in serializer.errors

    def test_submit_assignment_serializer_requires_file_for_file_submission_type(self):
        assignment = AssignmentFactory(submission_type=Assignment.SubmissionType.FILE)
        serializer = SubmitAssignmentSerializer(
            data={}, context={"assignment": assignment}
        )
        assert not serializer.is_valid()
        assert "non_field_errors" in serializer.errors
