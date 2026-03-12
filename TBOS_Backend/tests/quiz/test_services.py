"""Tests for quiz service layer."""
import pytest
from datetime import timedelta
from decimal import Decimal

from django.utils import timezone

from apps.quiz.models import Quiz, QuizAttempt, StudentAnswer, Question, Option
from apps.quiz.services.quiz_service import QuizService
from tests.factories import (
    CourseFactory,
    CourseSectionFactory,
    EnrollmentFactory,
    LessonFactory,
    OptionFactory,
    QuestionFactory,
    QuizAttemptFactory,
    QuizFactory,
    UserFactory,
)


# ──────────────────────────────────────────────
# Fixtures
# ──────────────────────────────────────────────


@pytest.fixture
def student(db):
    return UserFactory()


@pytest.fixture
def course(db):
    return CourseFactory()


@pytest.fixture
def quiz_lesson(course):
    from apps.lessons.models import Lesson
    section = CourseSectionFactory(course=course)
    return LessonFactory(section=section, lesson_type=Lesson.LessonType.QUIZ)


@pytest.fixture
def quiz(course, quiz_lesson):
    return QuizFactory(course=course, lesson=quiz_lesson, max_attempts=3, passing_score=50)


@pytest.fixture
def quiz_with_questions(quiz):
    """Quiz with 3 questions, each with 4 options (one correct)."""
    questions = []
    for i in range(3):
        q = QuestionFactory(quiz=quiz, question_text=f"Question {i+1}", order=i, points=1)
        OptionFactory(question=q, option_text="Wrong A", is_correct=False, order=0)
        OptionFactory(question=q, option_text="Wrong B", is_correct=False, order=1)
        OptionFactory(question=q, option_text="Wrong C", is_correct=False, order=2)
        OptionFactory(question=q, option_text="Correct", is_correct=True, order=3)
        questions.append(q)
    return quiz, questions


@pytest.fixture
def enrolled_student(student, course):
    EnrollmentFactory(student=student, course=course)
    return student


# ──────────────────────────────────────────────
# create_quiz
# ──────────────────────────────────────────────


@pytest.mark.django_db
class TestCreateQuiz:
    def test_create_quiz(self, course, quiz_lesson):
        quiz = QuizService.create_quiz(
            course=course,
            lesson=quiz_lesson,
            title="Test Quiz",
            description="A test quiz",
            max_attempts=2,
            passing_score=60,
        )
        assert quiz.pk is not None
        assert quiz.title == "Test Quiz"
        assert quiz.max_attempts == 2
        assert quiz.passing_score == 60


# ──────────────────────────────────────────────
# add_question / add_option
# ──────────────────────────────────────────────


@pytest.mark.django_db
class TestAddQuestionAndOption:
    def test_add_question(self, quiz):
        question = QuizService.add_question(
            quiz=quiz, question_text="What is Python?", points=2, order=0
        )
        assert question.pk is not None
        assert question.quiz == quiz
        assert question.points == 2

    def test_add_option(self, quiz):
        question = QuestionFactory(quiz=quiz)
        option = QuizService.add_option(
            question=question, option_text="A language", is_correct=True, order=0
        )
        assert option.pk is not None
        assert option.is_correct is True
        assert option.question == question


# ──────────────────────────────────────────────
# start_attempt
# ──────────────────────────────────────────────


@pytest.mark.django_db
class TestStartAttempt:
    def test_start_first_attempt(self, quiz_with_questions, enrolled_student):
        quiz, questions = quiz_with_questions
        attempt, created = QuizService.start_attempt(quiz=quiz, student=enrolled_student)
        assert created is True
        assert attempt.status == QuizAttempt.Status.IN_PROGRESS
        assert attempt.attempt_number == 1
        assert attempt.total_questions == 3
        assert attempt.total_points == 3

    def test_resume_existing_attempt(self, quiz_with_questions, enrolled_student):
        quiz, _ = quiz_with_questions
        attempt1, _ = QuizService.start_attempt(quiz=quiz, student=enrolled_student)
        attempt2, created = QuizService.start_attempt(quiz=quiz, student=enrolled_student)
        assert created is False
        assert attempt1.id == attempt2.id

    def test_start_second_attempt_after_submission(self, quiz_with_questions, enrolled_student):
        quiz, _ = quiz_with_questions
        attempt1, _ = QuizService.start_attempt(quiz=quiz, student=enrolled_student)
        QuizService.submit_quiz(attempt1)

        attempt2, created = QuizService.start_attempt(quiz=quiz, student=enrolled_student)
        assert created is True
        assert attempt2.attempt_number == 2

    def test_max_attempts_enforced(self, quiz_with_questions, enrolled_student):
        quiz, _ = quiz_with_questions
        quiz.max_attempts = 1
        quiz.save()

        attempt, _ = QuizService.start_attempt(quiz=quiz, student=enrolled_student)
        QuizService.submit_quiz(attempt)

        with pytest.raises(ValueError, match="Maximum attempts reached"):
            QuizService.start_attempt(quiz=quiz, student=enrolled_student)

    def test_unenrolled_student_cannot_attempt(self, quiz_with_questions):
        quiz, _ = quiz_with_questions
        unenrolled = UserFactory()
        with pytest.raises(ValueError, match="enrolled"):
            QuizService.start_attempt(quiz=quiz, student=unenrolled)


# ──────────────────────────────────────────────
# submit_answer
# ──────────────────────────────────────────────


@pytest.mark.django_db
class TestSubmitAnswer:
    def test_submit_correct_answer(self, quiz_with_questions, enrolled_student):
        quiz, questions = quiz_with_questions
        attempt, _ = QuizService.start_attempt(quiz=quiz, student=enrolled_student)

        correct_option = questions[0].options.get(is_correct=True)
        answer = QuizService.submit_answer(
            attempt=attempt,
            question_id=questions[0].id,
            option_id=correct_option.id,
        )
        assert answer.is_correct is True

    def test_submit_wrong_answer(self, quiz_with_questions, enrolled_student):
        quiz, questions = quiz_with_questions
        attempt, _ = QuizService.start_attempt(quiz=quiz, student=enrolled_student)

        wrong_option = questions[0].options.filter(is_correct=False).first()
        answer = QuizService.submit_answer(
            attempt=attempt,
            question_id=questions[0].id,
            option_id=wrong_option.id,
        )
        assert answer.is_correct is False

    def test_update_answer(self, quiz_with_questions, enrolled_student):
        quiz, questions = quiz_with_questions
        attempt, _ = QuizService.start_attempt(quiz=quiz, student=enrolled_student)

        wrong_option = questions[0].options.filter(is_correct=False).first()
        QuizService.submit_answer(
            attempt=attempt,
            question_id=questions[0].id,
            option_id=wrong_option.id,
        )

        correct_option = questions[0].options.get(is_correct=True)
        answer = QuizService.submit_answer(
            attempt=attempt,
            question_id=questions[0].id,
            option_id=correct_option.id,
        )
        assert answer.is_correct is True
        assert StudentAnswer.objects.filter(attempt=attempt, question=questions[0]).count() == 1

    def test_cannot_submit_after_completion(self, quiz_with_questions, enrolled_student):
        quiz, questions = quiz_with_questions
        attempt, _ = QuizService.start_attempt(quiz=quiz, student=enrolled_student)
        QuizService.submit_quiz(attempt)

        correct_option = questions[0].options.get(is_correct=True)
        with pytest.raises(ValueError, match="Cannot modify"):
            QuizService.submit_answer(
                attempt=attempt,
                question_id=questions[0].id,
                option_id=correct_option.id,
            )


# ──────────────────────────────────────────────
# submit_quiz (complete)
# ──────────────────────────────────────────────


@pytest.mark.django_db
class TestSubmitQuiz:
    def test_submit_perfect_score(self, quiz_with_questions, enrolled_student):
        quiz, questions = quiz_with_questions
        attempt, _ = QuizService.start_attempt(quiz=quiz, student=enrolled_student)

        for q in questions:
            correct = q.options.get(is_correct=True)
            QuizService.submit_answer(attempt=attempt, question_id=q.id, option_id=correct.id)

        attempt = QuizService.submit_quiz(attempt)
        assert attempt.status == QuizAttempt.Status.SUBMITTED
        assert attempt.score == 3
        assert attempt.correct_answers == 3
        assert attempt.percentage == Decimal("100.00")
        assert attempt.passed is True
        assert attempt.end_time is not None

    def test_submit_failing_score(self, quiz_with_questions, enrolled_student):
        quiz, questions = quiz_with_questions
        quiz.passing_score = 70
        quiz.save()

        attempt, _ = QuizService.start_attempt(quiz=quiz, student=enrolled_student)

        # Answer only 1 out of 3 correctly
        correct = questions[0].options.get(is_correct=True)
        QuizService.submit_answer(attempt=attempt, question_id=questions[0].id, option_id=correct.id)

        wrong = questions[1].options.filter(is_correct=False).first()
        QuizService.submit_answer(attempt=attempt, question_id=questions[1].id, option_id=wrong.id)

        attempt = QuizService.submit_quiz(attempt)
        assert attempt.passed is False
        assert attempt.correct_answers == 1

    def test_submit_empty_quiz(self, quiz_with_questions, enrolled_student):
        quiz, _ = quiz_with_questions
        attempt, _ = QuizService.start_attempt(quiz=quiz, student=enrolled_student)

        attempt = QuizService.submit_quiz(attempt)
        assert attempt.score == 0
        assert attempt.correct_answers == 0
        assert attempt.status == QuizAttempt.Status.SUBMITTED

    def test_double_submit_rejected(self, quiz_with_questions, enrolled_student):
        quiz, _ = quiz_with_questions
        attempt, _ = QuizService.start_attempt(quiz=quiz, student=enrolled_student)
        QuizService.submit_quiz(attempt)

        with pytest.raises(ValueError, match="already been submitted"):
            QuizService.submit_quiz(attempt)


# ──────────────────────────────────────────────
# calculate_score
# ──────────────────────────────────────────────


@pytest.mark.django_db
class TestCalculateScore:
    def test_calculate_score(self, quiz_with_questions, enrolled_student):
        quiz, questions = quiz_with_questions
        attempt, _ = QuizService.start_attempt(quiz=quiz, student=enrolled_student)

        for q in questions[:2]:
            correct = q.options.get(is_correct=True)
            QuizService.submit_answer(attempt=attempt, question_id=q.id, option_id=correct.id)

        result = QuizService.calculate_score(attempt)
        assert result["score"] == 2
        assert result["correct_answers"] == 2
        assert result["total_questions"] == 3


# ──────────────────────────────────────────────
# get_quiz_results
# ──────────────────────────────────────────────


@pytest.mark.django_db
class TestGetQuizResults:
    def test_get_results(self, quiz_with_questions, enrolled_student):
        quiz, questions = quiz_with_questions
        attempt, _ = QuizService.start_attempt(quiz=quiz, student=enrolled_student)
        QuizService.submit_quiz(attempt)

        results = QuizService.get_quiz_results(quiz, enrolled_student)
        assert results.count() == 1

    def test_no_results_before_submission(self, quiz_with_questions, enrolled_student):
        quiz, _ = quiz_with_questions
        QuizService.start_attempt(quiz=quiz, student=enrolled_student)

        results = QuizService.get_quiz_results(quiz, enrolled_student)
        assert results.count() == 0


# ──────────────────────────────────────────────
# Timer expiry
# ──────────────────────────────────────────────


@pytest.mark.django_db
class TestTimerExpiry:
    def test_expired_attempt_auto_submitted_on_start(self, quiz_with_questions, enrolled_student):
        quiz, _ = quiz_with_questions
        quiz.time_limit_minutes = 1
        quiz.save()

        attempt, _ = QuizService.start_attempt(quiz=quiz, student=enrolled_student)

        # Manually backdate start_time
        QuizAttempt.objects.filter(pk=attempt.pk).update(
            start_time=timezone.now() - timedelta(minutes=5)
        )

        # Starting again should expire the old attempt and create new one
        new_attempt, created = QuizService.start_attempt(quiz=quiz, student=enrolled_student)
        assert created is True
        assert new_attempt.id != attempt.id

        # Old attempt should be expired
        attempt.refresh_from_db()
        assert attempt.status == QuizAttempt.Status.EXPIRED

    def test_submit_answer_rejected_after_time_expired(self, quiz_with_questions, enrolled_student):
        quiz, questions = quiz_with_questions
        quiz.time_limit_minutes = 1
        quiz.save()

        attempt, _ = QuizService.start_attempt(quiz=quiz, student=enrolled_student)

        QuizAttempt.objects.filter(pk=attempt.pk).update(
            start_time=timezone.now() - timedelta(minutes=5)
        )
        attempt.refresh_from_db()

        correct = questions[0].options.get(is_correct=True)
        with pytest.raises(ValueError, match="expired"):
            QuizService.submit_answer(
                attempt=attempt,
                question_id=questions[0].id,
                option_id=correct.id,
            )
