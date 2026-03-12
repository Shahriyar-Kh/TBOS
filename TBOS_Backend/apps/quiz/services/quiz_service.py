import random

from django.db import transaction
from django.utils import timezone

from apps.enrollments.models import Enrollment
from apps.quiz.models import Quiz, QuizAttempt, StudentAnswer, Question, Option


class QuizService:

    # ── Quiz CRUD ────────────────────────────────

    @staticmethod
    def create_quiz(*, course, lesson, **kwargs) -> Quiz:
        return Quiz.objects.create(course=course, lesson=lesson, **kwargs)

    @staticmethod
    def add_question(*, quiz, **kwargs) -> Question:
        return Question.objects.create(quiz=quiz, **kwargs)

    @staticmethod
    def add_option(*, question, **kwargs) -> Option:
        return Option.objects.create(question=question, **kwargs)

    # ── Attempt workflow ─────────────────────────

    @staticmethod
    def start_attempt(quiz: Quiz, student) -> tuple[QuizAttempt, bool]:
        """
        Start or resume a quiz attempt.
        Returns (attempt, created).
        Validates enrollment and attempt limits.
        """
        # Check enrollment
        enrolled = Enrollment.objects.filter(
            student=student, course=quiz.course, is_active=True
        ).exists()
        if not enrolled:
            raise ValueError("You must be enrolled in the course to attempt this quiz.")

        # Resume existing in-progress attempt
        existing = QuizAttempt.objects.filter(
            quiz=quiz, student=student, status=QuizAttempt.Status.IN_PROGRESS
        ).first()
        if existing:
            # Check if time has expired
            if quiz.time_limit_minutes and existing.start_time:
                elapsed = (timezone.now() - existing.start_time).total_seconds() / 60
                if elapsed >= quiz.time_limit_minutes:
                    existing = QuizService._expire_attempt(existing)
                    # Fall through to create new attempt
                else:
                    return existing, False
            else:
                return existing, False

        # Check attempt limit
        completed_count = QuizAttempt.objects.filter(
            quiz=quiz,
            student=student,
            status__in=[QuizAttempt.Status.SUBMITTED, QuizAttempt.Status.EXPIRED],
        ).count()
        if completed_count >= quiz.max_attempts:
            raise ValueError("Maximum attempts reached.")

        total_points = sum(q.points for q in quiz.questions.all())
        total_questions = quiz.questions.count()

        attempt = QuizAttempt.objects.create(
            quiz=quiz,
            student=student,
            attempt_number=completed_count + 1,
            total_points=total_points,
            total_questions=total_questions,
        )
        return attempt, True

    @staticmethod
    def get_quiz_questions(quiz: Quiz):
        """Return questions, optionally shuffled."""
        questions = list(quiz.questions.prefetch_related("options").all())
        if quiz.shuffle_questions:
            random.shuffle(questions)
        return questions

    @staticmethod
    def submit_answer(attempt: QuizAttempt, question_id, option_id) -> StudentAnswer:
        """Submit or update a single answer within an active attempt."""
        if attempt.status != QuizAttempt.Status.IN_PROGRESS:
            raise ValueError("Cannot modify answers after submission.")

        # Check timer expiry
        if attempt.quiz.time_limit_minutes and attempt.start_time:
            elapsed = (timezone.now() - attempt.start_time).total_seconds() / 60
            if elapsed >= attempt.quiz.time_limit_minutes:
                QuizService._expire_attempt(attempt)
                raise ValueError("Time has expired. Quiz was auto-submitted.")

        question = Question.objects.get(id=question_id, quiz=attempt.quiz)
        option = Option.objects.get(id=option_id, question=question)

        answer, _ = StudentAnswer.objects.update_or_create(
            attempt=attempt,
            question=question,
            defaults={"selected_option": option, "is_correct": option.is_correct},
        )
        return answer

    @staticmethod
    @transaction.atomic
    def submit_quiz(attempt: QuizAttempt) -> QuizAttempt:
        """Submit the quiz attempt and calculate score."""
        if attempt.status != QuizAttempt.Status.IN_PROGRESS:
            raise ValueError("This attempt has already been submitted.")

        return QuizService._grade_attempt(attempt, QuizAttempt.Status.SUBMITTED)

    @staticmethod
    def calculate_score(attempt: QuizAttempt) -> dict:
        """Calculate and return score details without saving."""
        correct = attempt.answers.filter(is_correct=True).select_related("question")
        score = sum(a.question.points for a in correct)
        correct_count = correct.count()
        percentage = (score / attempt.total_points * 100) if attempt.total_points else 0
        return {
            "score": score,
            "correct_answers": correct_count,
            "total_questions": attempt.total_questions,
            "total_points": attempt.total_points,
            "percentage": round(percentage, 2),
            "passed": percentage >= attempt.quiz.passing_score,
        }

    @staticmethod
    def get_quiz_results(quiz: Quiz, student):
        """Get all completed attempts for a student on a quiz."""
        return QuizAttempt.objects.filter(
            quiz=quiz,
            student=student,
            status__in=[QuizAttempt.Status.SUBMITTED, QuizAttempt.Status.EXPIRED],
        ).prefetch_related("answers__question", "answers__selected_option").order_by("attempt_number")

    # ── Internal helpers ─────────────────────────

    @staticmethod
    @transaction.atomic
    def _expire_attempt(attempt: QuizAttempt) -> QuizAttempt:
        """Mark an attempt as expired and grade it."""
        return QuizService._grade_attempt(attempt, QuizAttempt.Status.EXPIRED)

    @staticmethod
    def _grade_attempt(attempt: QuizAttempt, final_status: str) -> QuizAttempt:
        """Score the attempt and set its final status."""
        correct = attempt.answers.filter(is_correct=True).select_related("question")
        score = sum(a.question.points for a in correct)
        correct_count = correct.count()
        percentage = (score / attempt.total_points * 100) if attempt.total_points else 0

        attempt.score = score
        attempt.correct_answers = correct_count
        attempt.percentage = round(percentage, 2)
        attempt.passed = percentage >= attempt.quiz.passing_score
        attempt.status = final_status
        attempt.end_time = timezone.now()
        attempt.save()
        return attempt
