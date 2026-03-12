"""Tests for assignment service layer."""
import pytest
from django.utils import timezone
from datetime import timedelta

from apps.assignments.models import Assignment, AssignmentGrade, AssignmentSubmission
from apps.assignments.services.assignment_service import AssignmentService
from apps.courses.models import Course
from tests.factories import (
    AssignmentFactory,
    AssignmentSubmissionFactory,
    CourseFactory,
    CourseSectionFactory,
    EnrollmentFactory,
    InstructorFactory,
    LessonFactory,
    UserFactory,
)
from apps.lessons.models import Lesson


@pytest.mark.django_db
class TestAssignmentServiceCreate:

    def test_create_assignment(self):
        instructor = InstructorFactory()
        course = CourseFactory(instructor=instructor, status=Course.Status.PUBLISHED)
        section = CourseSectionFactory(course=course)
        lesson = LessonFactory(section=section, lesson_type=Lesson.LessonType.ASSIGNMENT)

        assignment = AssignmentService.create_assignment({
            "course": course,
            "lesson": lesson,
            "title": "Final Project",
            "description": "Build a REST API",
            "instructions": "Use Django REST Framework.",
            "max_score": 100,
            "submission_type": Assignment.SubmissionType.FILE,
            "max_attempts": 2,
        })
        assert assignment.pk is not None
        assert assignment.title == "Final Project"
        assert assignment.max_attempts == 2

    def test_update_assignment(self):
        assignment = AssignmentFactory(title="Old Title")
        updated = AssignmentService.update_assignment(assignment, {"title": "New Title", "max_score": 50})
        assert updated.title == "New Title"
        assert updated.max_score == 50


@pytest.mark.django_db
class TestAssignmentServiceSubmit:

    def _setup(self):
        instructor = InstructorFactory()
        course = CourseFactory(instructor=instructor, status=Course.Status.PUBLISHED)
        section = CourseSectionFactory(course=course)
        lesson = LessonFactory(section=section, lesson_type=Lesson.LessonType.ASSIGNMENT)
        assignment = AssignmentFactory(
            course=course, lesson=lesson, max_attempts=3, allow_resubmission=True,
        )
        student = UserFactory()
        EnrollmentFactory(student=student, course=course)
        return assignment, student

    def test_submit_assignment_success(self):
        assignment, student = self._setup()
        sub = AssignmentService.submit_assignment(
            assignment, student, submission_text="My answer", file_url="https://s3.example.com/f.pdf",
        )
        assert sub.pk is not None
        assert sub.attempt_number == 1
        assert sub.status == AssignmentSubmission.Status.SUBMITTED

    def test_submit_multiple_attempts(self):
        assignment, student = self._setup()
        sub1 = AssignmentService.submit_assignment(assignment, student, submission_text="Attempt 1")
        sub2 = AssignmentService.submit_assignment(assignment, student, submission_text="Attempt 2")
        assert sub1.attempt_number == 1
        assert sub2.attempt_number == 2

    def test_submit_exceeds_max_attempts(self):
        assignment, student = self._setup()
        assignment.max_attempts = 1
        assignment.save()
        AssignmentService.submit_assignment(assignment, student, submission_text="First")
        with pytest.raises(ValueError, match="Maximum attempts"):
            AssignmentService.submit_assignment(assignment, student, submission_text="Second")

    def test_submit_not_enrolled(self):
        assignment = AssignmentFactory()
        student = UserFactory()
        with pytest.raises(ValueError, match="enrolled"):
            AssignmentService.submit_assignment(assignment, student, submission_text="Test")

    def test_submit_resubmission_not_allowed(self):
        assignment, student = self._setup()
        assignment.allow_resubmission = False
        assignment.max_attempts = 1
        assignment.save()
        AssignmentService.submit_assignment(assignment, student, submission_text="First")
        with pytest.raises(ValueError, match="Resubmission is not allowed"):
            AssignmentService.submit_assignment(assignment, student, submission_text="Second")

    def test_submit_after_deadline_marked_late(self):
        assignment, student = self._setup()
        assignment.due_date = timezone.now() - timedelta(days=1)
        assignment.save()
        sub = AssignmentService.submit_assignment(assignment, student, submission_text="Late work")
        assert sub.status == AssignmentSubmission.Status.LATE

    def test_submit_before_deadline_marked_submitted(self):
        assignment, student = self._setup()
        assignment.due_date = timezone.now() + timedelta(days=7)
        assignment.save()
        sub = AssignmentService.submit_assignment(assignment, student, submission_text="On time")
        assert sub.status == AssignmentSubmission.Status.SUBMITTED


@pytest.mark.django_db
class TestAssignmentServiceGrade:

    def test_grade_submission(self):
        instructor = InstructorFactory()
        course = CourseFactory(instructor=instructor, status=Course.Status.PUBLISHED)
        assignment = AssignmentFactory(course=course, max_score=100)
        student = UserFactory()
        EnrollmentFactory(student=student, course=course)
        sub = AssignmentSubmissionFactory(assignment=assignment, student=student)

        grade = AssignmentService.grade_submission(sub, score=85, feedback="Good job!", graded_by=instructor)
        assert grade.score == 85
        assert grade.feedback == "Good job!"
        assert grade.grader == instructor
        sub.refresh_from_db()
        assert sub.status == AssignmentSubmission.Status.GRADED

    def test_grade_exceeds_max_score(self):
        assignment = AssignmentFactory(max_score=100)
        sub = AssignmentSubmissionFactory(assignment=assignment)
        instructor = InstructorFactory()
        with pytest.raises(ValueError, match="Score cannot exceed"):
            AssignmentService.grade_submission(sub, score=150, feedback="", graded_by=instructor)

    def test_regrade_submission(self):
        instructor = InstructorFactory()
        sub = AssignmentSubmissionFactory()
        grade1 = AssignmentService.grade_submission(sub, score=70, feedback="Needs work", graded_by=instructor)
        grade2 = AssignmentService.grade_submission(sub, score=85, feedback="Improved", graded_by=instructor)
        assert grade1.pk == grade2.pk
        assert grade2.score == 85
        assert grade2.feedback == "Improved"


@pytest.mark.django_db
class TestAssignmentServiceQueries:

    def test_get_assignment_submissions(self):
        assignment = AssignmentFactory()
        s1 = UserFactory()
        s2 = UserFactory()
        AssignmentSubmissionFactory(assignment=assignment, student=s1, attempt_number=1)
        AssignmentSubmissionFactory(assignment=assignment, student=s2, attempt_number=1)
        subs = AssignmentService.get_assignment_submissions(assignment)
        assert subs.count() == 2

    def test_get_student_submissions(self):
        assignment = AssignmentFactory()
        student = UserFactory()
        AssignmentSubmissionFactory(assignment=assignment, student=student, attempt_number=1)
        AssignmentSubmissionFactory(assignment=assignment, student=student, attempt_number=2)
        subs = AssignmentService.get_student_submissions(assignment, student)
        assert subs.count() == 2
        assert list(subs.values_list("attempt_number", flat=True)) == [1, 2]
