import logging

from django.db import transaction
from django.utils import timezone

from apps.assignments.models import Assignment, AssignmentGrade, AssignmentSubmission
from apps.enrollments.models import Enrollment

logger = logging.getLogger(__name__)


class AssignmentService:
    """Encapsulates all assignment business logic."""

    # ──────────────────────────────────────────────
    # Assignment CRUD
    # ──────────────────────────────────────────────

    @staticmethod
    def create_assignment(validated_data: dict) -> Assignment:
        assignment = Assignment.objects.create(**validated_data)
        logger.info("Assignment created: %s (id=%s)", assignment.title, assignment.id)
        return assignment

    @staticmethod
    def update_assignment(assignment: Assignment, validated_data: dict) -> Assignment:
        for field, value in validated_data.items():
            setattr(assignment, field, value)
        assignment.save()
        logger.info("Assignment updated: %s (id=%s)", assignment.title, assignment.id)
        return assignment

    # ──────────────────────────────────────────────
    # Submission
    # ──────────────────────────────────────────────

    @staticmethod
    def submit_assignment(
        assignment: Assignment,
        student,
        submission_text: str = "",
        file_url: str = "",
    ) -> AssignmentSubmission:
        """
        Create a new submission for an assignment.
        Enforces enrollment, attempt limits, resubmission rules, and deadline.
        """
        # 1. Student must be enrolled
        course = assignment.course
        is_enrolled = Enrollment.objects.filter(
            student=student, course=course, is_active=True
        ).exists()
        if not is_enrolled:
            raise ValueError("You must be enrolled in the course to submit.")

        # 2. Count existing attempts
        existing_count = AssignmentSubmission.objects.filter(
            assignment=assignment, student=student
        ).count()

        # 3. Resubmission check
        if not assignment.allow_resubmission and existing_count >= 1:
            raise ValueError("Resubmission is not allowed for this assignment.")

        # 4. Max attempts check
        if existing_count >= assignment.max_attempts:
            raise ValueError(
                f"Maximum attempts ({assignment.max_attempts}) reached."
            )

        # 5. Determine status based on deadline
        now = timezone.now()
        status = AssignmentSubmission.Status.SUBMITTED
        if assignment.due_date and now > assignment.due_date:
            status = AssignmentSubmission.Status.LATE

        submission = AssignmentSubmission.objects.create(
            assignment=assignment,
            student=student,
            submission_text=submission_text,
            file_url=file_url,
            attempt_number=existing_count + 1,
            status=status,
            submitted_at=now,
        )
        logger.info(
            "Submission created: student=%s assignment=%s attempt=%d status=%s",
            student.email, assignment.title, submission.attempt_number, status,
        )
        return submission

    # ──────────────────────────────────────────────
    # Grading
    # ──────────────────────────────────────────────

    @staticmethod
    @transaction.atomic
    def grade_submission(
        submission: AssignmentSubmission,
        score: int,
        feedback: str,
        graded_by,
    ) -> AssignmentGrade:
        """Grade a submission. Creates or updates the AssignmentGrade."""
        max_score = submission.assignment.max_score
        if score > max_score:
            raise ValueError(f"Score cannot exceed {max_score}.")

        grade, created = AssignmentGrade.objects.update_or_create(
            submission=submission,
            defaults={
                "grader": graded_by,
                "score": score,
                "feedback": feedback,
                "graded_at": timezone.now(),
            },
        )

        # Mark submission as graded
        submission.status = AssignmentSubmission.Status.GRADED
        submission.save(update_fields=["status", "updated_at"])

        logger.info(
            "Submission graded: id=%s score=%d/%d by=%s",
            submission.id, score, max_score, graded_by.email,
        )
        return grade

    # ──────────────────────────────────────────────
    # Queries
    # ──────────────────────────────────────────────

    @staticmethod
    def get_assignment_submissions(assignment: Assignment):
        """Return all submissions for an assignment (instructor view)."""
        return (
            AssignmentSubmission.objects.filter(assignment=assignment)
            .select_related("student", "grade")
            .order_by("student__email", "attempt_number")
        )

    @staticmethod
    def get_student_submissions(assignment: Assignment, student):
        """Return all submissions by a student for an assignment."""
        return (
            AssignmentSubmission.objects.filter(
                assignment=assignment, student=student
            )
            .select_related("grade")
            .order_by("attempt_number")
        )
