from datetime import timedelta

import pytest
from django.utils import timezone

from apps.assignments.services.assignment_service import AssignmentService
from apps.certificates.services.certificate_service import CertificateService
from apps.enrollments.models import Enrollment
from apps.enrollments.services.enrollment_service import EnrollmentService
from apps.quiz.services.quiz_service import QuizService
from apps.reviews.services.review_service import ReviewService
from tests.factories import (
    AssignmentFactory,
    CourseFactory,
    LessonFactory,
    OptionFactory,
    QuestionFactory,
    QuizFactory,
    UserFactory,
    VideoFactory,
)


@pytest.mark.django_db
class TestEndToEndWorkflow:
    def test_learning_journey_from_enrollment_to_certificate(self, settings):
        settings.FRONTEND_URL = "http://localhost:3000"

        instructor = UserFactory(role="instructor")
        student = UserFactory(role="student")
        course = CourseFactory(instructor=instructor, status="published", is_free=True)

        lesson = LessonFactory(section__course=course, is_preview=False)
        VideoFactory(lesson=lesson, course=course, duration_seconds=300)

        quiz = QuizFactory(course=course, lesson=LessonFactory(section__course=course, lesson_type="quiz"), is_active=True)
        question = QuestionFactory(quiz=quiz, points=2)
        correct_option = OptionFactory(question=question, is_correct=True)

        assignment = AssignmentFactory(
            course=course,
            lesson=LessonFactory(section__course=course, lesson_type="assignment"),
            due_date=timezone.now() + timedelta(days=1),
            is_published=True,
        )

        enrollment = EnrollmentService.enroll_student(student, course)
        enrollment = EnrollmentService.mark_lesson_completed(enrollment, lesson)

        attempt, _ = QuizService.start_attempt(quiz=quiz, student=student)
        QuizService.submit_answer(attempt=attempt, question_id=question.id, option_id=correct_option.id)
        attempt = QuizService.submit_quiz(attempt)
        assert attempt.passed is True

        submission = AssignmentService.submit_assignment(
            assignment=assignment,
            student=student,
            submission_text="My solution",
            file_url="https://files.example.com/solution.pdf",
        )
        AssignmentService.grade_submission(
            submission=submission,
            score=90,
            feedback="Great work",
            graded_by=instructor,
        )

        enrollment.enrollment_status = Enrollment.EnrollmentStatus.COMPLETED
        enrollment.total_lessons_count = 1
        enrollment.completed_lessons_count = 1
        enrollment.completed_at = timezone.now()
        enrollment.save(update_fields=["enrollment_status", "total_lessons_count", "completed_lessons_count", "completed_at", "updated_at"])

        cert = CertificateService.generate_for_enrollment(enrollment)
        assert cert is not None

        review = ReviewService.create_review(student=student, course=course, rating=5, review_text="Excellent")
        assert review.rating == 5

    def test_paid_course_order_then_enrollment(self):
        student = UserFactory(role="student")
        course = CourseFactory(status="published", is_free=False, price=100, discount=0)

        enrollment = EnrollmentService.enroll_paid_course(student, course)
        assert enrollment.course == course
        assert Enrollment.objects.filter(student=student, course=course).exists()
