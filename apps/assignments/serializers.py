from django.utils import timezone
from rest_framework import serializers

from apps.assignments.models import Assignment, Submission


class AssignmentSerializer(serializers.ModelSerializer):
    submission_count = serializers.SerializerMethodField()

    class Meta:
        model = Assignment
        fields = [
            "id",
            "course",
            "lesson",
            "title",
            "description",
            "instructions_url",
            "max_score",
            "due_date",
            "time_limit_minutes",
            "is_published",
            "order",
            "submission_count",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def get_submission_count(self, obj):
        return obj.submissions.count()


class AssignmentListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Assignment
        fields = [
            "id",
            "title",
            "due_date",
            "max_score",
            "is_published",
            "order",
        ]


class SubmissionSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(
        source="student.full_name", read_only=True
    )

    class Meta:
        model = Submission
        fields = [
            "id",
            "assignment",
            "student",
            "student_name",
            "submission_text",
            "file_url",
            "status",
            "score",
            "feedback",
            "graded_by",
            "graded_at",
            "submitted_at",
            "started_at",
            "created_at",
        ]
        read_only_fields = [
            "id",
            "student",
            "graded_by",
            "graded_at",
            "started_at",
            "created_at",
        ]


class SubmitAssignmentSerializer(serializers.Serializer):
    submission_text = serializers.CharField(required=False, default="")
    file_url = serializers.URLField(required=False, default="")

    def validate(self, attrs):
        if not attrs.get("submission_text") and not attrs.get("file_url"):
            raise serializers.ValidationError(
                "Either submission_text or file_url is required."
            )
        return attrs


class GradeSubmissionSerializer(serializers.Serializer):
    score = serializers.IntegerField(min_value=0)
    feedback = serializers.CharField(required=False, default="")
