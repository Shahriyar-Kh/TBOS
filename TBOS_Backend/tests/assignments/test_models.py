"""Tests for assignment models."""
import pytest
from django.utils import timezone

from apps.assignments.models import Assignment, AssignmentGrade, AssignmentSubmission
from apps.lessons.models import Lesson
from tests.factories import (
    AssignmentFactory,
    AssignmentGradeFactory,
    AssignmentSubmissionFactory,
    CourseFactory,
    CourseSectionFactory,
    InstructorFactory,
    LessonFactory,
    UserFactory,
)


@pytest.mark.django_db
class TestAssignmentModel:

    def test_create_assignment(self):
        assignment = AssignmentFactory()
        assert assignment.pk is not None
        assert assignment.title.startswith("Assignment")
        assert assignment.max_score == 100
        assert assignment.submission_type == Assignment.SubmissionType.FILE_AND_TEXT
        assert assignment.allow_resubmission is True
        assert assignment.max_attempts == 3

    def test_assignment_str(self):
        assignment = AssignmentFactory(title="Homework 1")
        assert "Homework 1" in str(assignment)

    def test_submission_type_choices(self):
        for st in [Assignment.SubmissionType.FILE, Assignment.SubmissionType.TEXT, Assignment.SubmissionType.FILE_AND_TEXT]:
            a = AssignmentFactory(submission_type=st)
            assert a.submission_type == st

    def test_assignment_belongs_to_lesson(self):
        instructor = InstructorFactory()
        course = CourseFactory(instructor=instructor)
        section = CourseSectionFactory(course=course)
        lesson = LessonFactory(section=section, lesson_type=Lesson.LessonType.ASSIGNMENT)
        assignment = AssignmentFactory(course=course, lesson=lesson)
        assert assignment.lesson == lesson
        assert assignment.course == course

    def test_assignment_ordering(self):
        course = CourseFactory()
        a1 = AssignmentFactory(course=course, order=2)
        a2 = AssignmentFactory(course=course, order=1)
        qs = Assignment.objects.filter(course=course)
        assert list(qs) == [a2, a1]

    def test_assignment_defaults(self):
        assignment = AssignmentFactory()
        assert assignment.is_published is True  # factory default
        assert assignment.allow_resubmission is True
        assert assignment.max_attempts == 3


@pytest.mark.django_db
class TestAssignmentSubmissionModel:

    def test_create_submission(self):
        sub = AssignmentSubmissionFactory()
        assert sub.pk is not None
        assert sub.attempt_number == 1
        assert sub.status == AssignmentSubmission.Status.SUBMITTED

    def test_submission_str(self):
        sub = AssignmentSubmissionFactory()
        assert sub.student.email in str(sub)
        assert sub.assignment.title in str(sub)

    def test_multiple_attempts(self):
        student = UserFactory()
        assignment = AssignmentFactory()
        sub1 = AssignmentSubmissionFactory(assignment=assignment, student=student, attempt_number=1)
        sub2 = AssignmentSubmissionFactory(assignment=assignment, student=student, attempt_number=2)
        assert sub1.attempt_number == 1
        assert sub2.attempt_number == 2

    def test_unique_together_constraint(self):
        student = UserFactory()
        assignment = AssignmentFactory()
        AssignmentSubmissionFactory(assignment=assignment, student=student, attempt_number=1)
        with pytest.raises(Exception):
            AssignmentSubmissionFactory(assignment=assignment, student=student, attempt_number=1)

    def test_submission_status_choices(self):
        for s in [AssignmentSubmission.Status.SUBMITTED, AssignmentSubmission.Status.GRADED,
                   AssignmentSubmission.Status.LATE, AssignmentSubmission.Status.REJECTED]:
            sub = AssignmentSubmissionFactory(status=s)
            assert sub.status == s

    def test_submission_relationship(self):
        assignment = AssignmentFactory()
        sub = AssignmentSubmissionFactory(assignment=assignment)
        assert sub in assignment.submissions.all()


@pytest.mark.django_db
class TestAssignmentGradeModel:

    def test_create_grade(self):
        grade = AssignmentGradeFactory()
        assert grade.pk is not None
        assert grade.score == 85

    def test_grade_str(self):
        grade = AssignmentGradeFactory(score=90)
        assert "90" in str(grade)

    def test_grade_one_to_one(self):
        sub = AssignmentSubmissionFactory()
        grade = AssignmentGradeFactory(submission=sub)
        assert sub.grade == grade

    def test_grade_with_feedback(self):
        grade = AssignmentGradeFactory(feedback="Great work!")
        assert grade.feedback == "Great work!"
