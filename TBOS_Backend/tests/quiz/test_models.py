"""Tests for quiz models."""
import pytest

from apps.quiz.models import Quiz, Question, Option, QuizAttempt, StudentAnswer
from tests.factories import (
    CourseFactory,
    CourseSectionFactory,
    LessonFactory,
    OptionFactory,
    QuestionFactory,
    QuizAttemptFactory,
    QuizFactory,
    StudentAnswerFactory,
    UserFactory,
)


@pytest.mark.django_db
class TestQuizModel:
    def test_create_quiz(self):
        quiz = QuizFactory()
        assert quiz.pk is not None
        assert quiz.title.startswith("Quiz")
        assert quiz.max_attempts == 3
        assert quiz.passing_score == 50
        assert quiz.is_active is True
        assert quiz.shuffle_questions is False
        assert quiz.shuffle_options is False

    def test_str_representation(self):
        quiz = QuizFactory(title="My Quiz")
        assert str(quiz) == "My Quiz"

    def test_time_limit_nullable(self):
        quiz = QuizFactory(time_limit_minutes=None)
        assert quiz.time_limit_minutes is None

    def test_defaults(self):
        quiz = QuizFactory()
        assert quiz.description == "" or quiz.description
        assert quiz.created_at is not None
        assert quiz.updated_at is not None


@pytest.mark.django_db
class TestQuestionModel:
    def test_create_question(self):
        question = QuestionFactory()
        assert question.pk is not None
        assert question.question_type == "mcq"
        assert question.points == 1

    def test_str_representation(self):
        question = QuestionFactory(question_text="What is Django?")
        assert "What is Django?" in str(question)

    def test_question_belongs_to_quiz(self):
        quiz = QuizFactory()
        question = QuestionFactory(quiz=quiz)
        assert question.quiz == quiz
        assert question in quiz.questions.all()

    def test_explanation_field(self):
        question = QuestionFactory(explanation="This is explained by...")
        assert question.explanation == "This is explained by..."


@pytest.mark.django_db
class TestOptionModel:
    def test_create_option(self):
        option = OptionFactory()
        assert option.pk is not None
        assert option.is_correct is False

    def test_correct_option(self):
        option = OptionFactory(is_correct=True)
        assert option.is_correct is True

    def test_option_belongs_to_question(self):
        question = QuestionFactory()
        option = OptionFactory(question=question)
        assert option.question == question
        assert option in question.options.all()

    def test_str_representation(self):
        option = OptionFactory(option_text="Option A")
        assert str(option) == "Option A"


@pytest.mark.django_db
class TestQuizAttemptModel:
    def test_create_attempt(self):
        attempt = QuizAttemptFactory()
        assert attempt.pk is not None
        assert attempt.status == QuizAttempt.Status.IN_PROGRESS
        assert attempt.attempt_number == 1
        assert attempt.score == 0

    def test_is_completed_property(self):
        attempt = QuizAttemptFactory(status=QuizAttempt.Status.SUBMITTED)
        assert attempt.is_completed is True

        attempt2 = QuizAttemptFactory(status=QuizAttempt.Status.EXPIRED)
        assert attempt2.is_completed is True

        attempt3 = QuizAttemptFactory(status=QuizAttempt.Status.IN_PROGRESS)
        assert attempt3.is_completed is False

    def test_str_representation(self):
        attempt = QuizAttemptFactory()
        result = str(attempt)
        assert attempt.student.email in result
        assert attempt.quiz.title in result

    def test_status_choices(self):
        choices = [c[0] for c in QuizAttempt.Status.choices]
        assert "in_progress" in choices
        assert "submitted" in choices
        assert "expired" in choices


@pytest.mark.django_db
class TestStudentAnswerModel:
    def test_create_answer(self):
        answer = StudentAnswerFactory()
        assert answer.pk is not None
        assert answer.is_correct is False

    def test_unique_together(self):
        attempt = QuizAttemptFactory()
        question = QuestionFactory(quiz=attempt.quiz)
        option = OptionFactory(question=question)
        StudentAnswerFactory(attempt=attempt, question=question, selected_option=option)

        with pytest.raises(Exception):
            StudentAnswerFactory(attempt=attempt, question=question, selected_option=option)

    def test_str_representation(self):
        answer = StudentAnswerFactory()
        result = str(answer)
        assert "Correct:" in result
