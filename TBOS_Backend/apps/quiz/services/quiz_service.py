from django.utils import timezone

from apps.quiz.models import Quiz, QuizAttempt, QuizAnswer, Question, Option


class QuizService:
    @staticmethod
    def start_attempt(quiz: Quiz, student) -> tuple[QuizAttempt, bool]:
        """
        Start or resume a quiz attempt.
        Returns (attempt, created).
        """
        existing = QuizAttempt.objects.filter(
            quiz=quiz, student=student, is_completed=False
        ).first()
        if existing:
            return existing, False

        completed_count = QuizAttempt.objects.filter(
            quiz=quiz, student=student, is_completed=True
        ).count()
        if completed_count >= quiz.max_attempts:
            raise ValueError("Maximum attempts reached.")

        total_points = sum(q.points for q in quiz.questions.all())
        attempt = QuizAttempt.objects.create(
            quiz=quiz,
            student=student,
            total_points=total_points,
        )
        return attempt, True

    @staticmethod
    def submit_answer(
        attempt: QuizAttempt, question_id, option_id
    ) -> QuizAnswer:
        question = Question.objects.get(id=question_id)
        option = Option.objects.get(id=option_id)

        answer, _ = QuizAnswer.objects.update_or_create(
            attempt=attempt,
            question=question,
            defaults={"selected_option": option, "is_correct": option.is_correct},
        )
        return answer

    @staticmethod
    def complete_attempt(attempt: QuizAttempt) -> QuizAttempt:
        correct = attempt.answers.filter(is_correct=True).select_related("question")
        score = sum(a.question.points for a in correct)
        percentage = (score / attempt.total_points * 100) if attempt.total_points else 0

        attempt.score = score
        attempt.percentage = round(percentage, 2)
        attempt.passed = percentage >= attempt.quiz.pass_percentage
        attempt.is_completed = True
        attempt.completed_at = timezone.now()
        attempt.save()
        return attempt
