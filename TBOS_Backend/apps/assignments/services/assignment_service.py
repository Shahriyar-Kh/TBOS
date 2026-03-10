from django.utils import timezone

from apps.assignments.models import Assignment, Submission


class AssignmentService:
    @staticmethod
    def submit_assignment(
        assignment: Assignment, student, submission_text: str = "", file_url: str = ""
    ) -> Submission:
        submission, created = Submission.objects.get_or_create(
            assignment=assignment,
            student=student,
            defaults={
                "submission_text": submission_text,
                "file_url": file_url,
                "status": Submission.Status.SUBMITTED,
                "submitted_at": timezone.now(),
            },
        )
        if not created:
            if submission.status == Submission.Status.GRADED:
                raise ValueError("Assignment already graded.")
            submission.submission_text = submission_text or submission.submission_text
            submission.file_url = file_url or submission.file_url
            submission.status = Submission.Status.SUBMITTED
            submission.submitted_at = timezone.now()
            submission.save()

        return submission

    @staticmethod
    def grade_submission(
        submission: Submission, score: int, feedback: str, graded_by
    ) -> Submission:
        if score > submission.assignment.max_score:
            raise ValueError(
                f"Score cannot exceed {submission.assignment.max_score}."
            )

        submission.score = score
        submission.feedback = feedback
        submission.status = Submission.Status.GRADED
        submission.graded_by = graded_by
        submission.graded_at = timezone.now()
        submission.save()
        return submission
