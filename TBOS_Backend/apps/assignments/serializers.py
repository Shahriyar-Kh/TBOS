from rest_framework import serializers

from apps.assignments.models import Assignment, AssignmentGrade, AssignmentSubmission


# ──────────────────────────────────────────────
# Instructor serializers
# ──────────────────────────────────────────────


class AssignmentCreateSerializer(serializers.ModelSerializer):
    """Used by instructors to create / update assignments."""

    class Meta:
        model = Assignment
        fields = [
            "course",
            "lesson",
            "title",
            "description",
            "instructions",
            "max_score",
            "submission_type",
            "due_date",
            "allow_resubmission",
            "max_attempts",
            "time_limit_minutes",
            "is_published",
            "order",
        ]

    def validate_max_attempts(self, value):
        if value < 1:
            raise serializers.ValidationError("max_attempts must be at least 1.")
        return value


class AssignmentSerializer(serializers.ModelSerializer):
    """Full representation for instructor views."""

    submission_count = serializers.SerializerMethodField()

    class Meta:
        model = Assignment
        fields = [
            "id",
            "course",
            "lesson",
            "title",
            "description",
            "instructions",
            "instructions_url",
            "max_score",
            "submission_type",
            "due_date",
            "allow_resubmission",
            "max_attempts",
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
    """Compact assignment representation for list views."""

    class Meta:
        model = Assignment
        fields = [
            "id",
            "title",
            "description",
            "submission_type",
            "due_date",
            "max_score",
            "max_attempts",
            "allow_resubmission",
            "is_published",
            "order",
        ]


# ──────────────────────────────────────────────
# Submission serializers
# ──────────────────────────────────────────────

ALLOWED_FILE_EXTENSIONS = (".pdf", ".zip", ".docx", ".py")
MAX_FILE_SIZE_MB = 25


class SubmitAssignmentSerializer(serializers.Serializer):
    """Used by students to submit assignments."""

    submission_text = serializers.CharField(required=False, default="")
    file_url = serializers.URLField(required=False, default="")

    def validate_file_url(self, value):
        if value:
            lower = value.lower().split("?")[0]  # strip query params
            if not any(lower.endswith(ext) for ext in ALLOWED_FILE_EXTENSIONS):
                raise serializers.ValidationError(
                    f"File type not allowed. Accepted: {', '.join(ALLOWED_FILE_EXTENSIONS)}"
                )
        return value

    def validate(self, attrs):
        assignment = self.context.get("assignment")
        text = attrs.get("submission_text")
        file_url = attrs.get("file_url")

        if assignment:
            st = assignment.submission_type
            if st == Assignment.SubmissionType.FILE and not file_url:
                raise serializers.ValidationError(
                    "This assignment requires a file upload."
                )
            if st == Assignment.SubmissionType.TEXT and not text:
                raise serializers.ValidationError(
                    "This assignment requires a text submission."
                )
            if st == Assignment.SubmissionType.FILE_AND_TEXT and (not text or not file_url):
                raise serializers.ValidationError(
                    "This assignment requires both text and file upload."
                )
        elif not text and not file_url:
            raise serializers.ValidationError(
                "Either submission_text or file_url is required."
            )
        return attrs


class AssignmentSubmissionSerializer(serializers.ModelSerializer):
    """Read serializer for submissions."""

    student_name = serializers.CharField(source="student.full_name", read_only=True)
    grade = serializers.SerializerMethodField()

    class Meta:
        model = AssignmentSubmission
        fields = [
            "id",
            "assignment",
            "student",
            "student_name",
            "submission_text",
            "file_url",
            "attempt_number",
            "status",
            "submitted_at",
            "grade",
            "created_at",
        ]
        read_only_fields = [
            "id",
            "student",
            "attempt_number",
            "status",
            "submitted_at",
            "created_at",
        ]

    def get_grade(self, obj):
        try:
            g = obj.grade
            return {
                "id": str(g.id),
                "score": g.score,
                "feedback": g.feedback,
                "grader": str(g.grader_id),
                "graded_at": g.graded_at.isoformat() if g.graded_at else None,
            }
        except AssignmentGrade.DoesNotExist:
            return None


# ──────────────────────────────────────────────
# Grading serializers
# ──────────────────────────────────────────────


class AssignmentGradeSerializer(serializers.Serializer):
    """Used by instructors to grade a submission."""

    submission_id = serializers.UUIDField()
    score = serializers.IntegerField(min_value=0)
    feedback = serializers.CharField(required=False, default="")


class AssignmentGradeDetailSerializer(serializers.ModelSerializer):
    """Read serializer for grade details."""

    class Meta:
        model = AssignmentGrade
        fields = [
            "id",
            "submission",
            "grader",
            "score",
            "feedback",
            "graded_at",
            "created_at",
        ]
        read_only_fields = fields
