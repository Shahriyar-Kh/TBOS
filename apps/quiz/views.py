from django.utils import timezone
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response

from apps.core.permissions import IsAdminOrInstructor, IsStudent
from apps.quiz.models import Option, Question, Quiz, QuizAnswer, QuizAttempt
from apps.quiz.services.quiz_service import QuizService
from apps.quiz.serializers import (
    QuestionSerializer,
    QuizAttemptSerializer,
    QuizDetailSerializer,
    QuizResultSerializer,
    QuizSerializer,
    QuestionStudentSerializer,
    SubmitAnswerSerializer,
    OptionSerializer,
)


# ──────────────────────────────────────────────
# Instructor / Admin
# ──────────────────────────────────────────────
class InstructorQuizViewSet(viewsets.ModelViewSet):
    """
    /api/v1/quiz/instructor/quizzes/
    Full CRUD for quizzes (instructor owns the course).
    """
    serializer_class = QuizSerializer
    permission_classes = [IsAuthenticated, IsAdminOrInstructor]

    def get_serializer_class(self):
        if self.action == "retrieve":
            return QuizDetailSerializer
        return QuizSerializer

    def get_queryset(self):
        user = self.request.user
        qs = Quiz.objects.select_related("course", "lesson").prefetch_related("questions__options")
        if user.role == "instructor":
            qs = qs.filter(course__instructor=user)
        course_id = self.request.query_params.get("course")
        if course_id:
            qs = qs.filter(course_id=course_id)
        return qs


class InstructorQuestionViewSet(viewsets.ModelViewSet):
    """
    /api/v1/quiz/instructor/questions/
    """
    serializer_class = QuestionSerializer
    permission_classes = [IsAuthenticated, IsAdminOrInstructor]

    def get_queryset(self):
        user = self.request.user
        qs = Question.objects.select_related("quiz__course").prefetch_related("options")
        if user.role == "instructor":
            qs = qs.filter(quiz__course__instructor=user)
        quiz_id = self.request.query_params.get("quiz")
        if quiz_id:
            qs = qs.filter(quiz_id=quiz_id)
        return qs


class InstructorOptionViewSet(viewsets.ModelViewSet):
    """
    /api/v1/quiz/instructor/options/
    """
    serializer_class = OptionSerializer
    permission_classes = [IsAuthenticated, IsAdminOrInstructor]

    def get_queryset(self):
        qs = Option.objects.select_related("question__quiz__course")
        question_id = self.request.query_params.get("question")
        if question_id:
            qs = qs.filter(question_id=question_id)
        return qs


# ──────────────────────────────────────────────
# Student quiz taking
# ──────────────────────────────────────────────
class StudentQuizViewSet(viewsets.ReadOnlyModelViewSet):
    """
    /api/v1/quiz/student/
    List published quizzes for enrolled courses.
    """
    serializer_class = QuizSerializer
    permission_classes = [IsAuthenticated, IsStudent]

    def get_queryset(self):
        enrolled_courses = self.request.user.enrollments.filter(
            is_active=True
        ).values_list("course_id", flat=True)
        return Quiz.objects.filter(
            course_id__in=enrolled_courses, is_published=True
        )

    @action(detail=True, methods=["post"])
    def start(self, request, pk=None):
        """Start a quiz attempt."""
        quiz = self.get_object()
        try:
            attempt, created = QuizService.start_attempt(quiz=quiz, student=request.user)
        except ValueError as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            QuizAttemptSerializer(attempt).data,
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )

    @action(detail=True, methods=["get"], url_path="questions")
    def get_questions(self, request, pk=None):
        """Get questions for an active attempt (no correct answers shown)."""
        quiz = self.get_object()
        questions = quiz.questions.prefetch_related("options").all()
        return Response(QuestionStudentSerializer(questions, many=True).data)

    @action(detail=True, methods=["post"], url_path="submit-answer")
    def submit_answer(self, request, pk=None):
        """Submit an answer for one question in an active attempt."""
        quiz = self.get_object()
        serializer = SubmitAnswerSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        attempt = QuizAttempt.objects.filter(
            quiz=quiz, student=request.user, is_completed=False
        ).first()
        if not attempt:
            return Response(
                {"detail": "No active attempt found."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        answer = QuizService.submit_answer(
            attempt=attempt,
            question_id=serializer.validated_data["question_id"],
            option_id=serializer.validated_data["option_id"],
        )

        return Response(
            {"submitted": True, "answer_id": str(answer.id)},
            status=status.HTTP_200_OK,
        )

    @action(detail=True, methods=["post"])
    def complete(self, request, pk=None):
        """Complete a quiz attempt and calculate score."""
        quiz = self.get_object()
        attempt = QuizAttempt.objects.filter(
            quiz=quiz, student=request.user, is_completed=False
        ).first()
        if not attempt:
            return Response(
                {"detail": "No active attempt found."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        attempt = QuizService.complete_attempt(attempt)

        return Response(QuizResultSerializer(attempt).data)

    @action(detail=True, methods=["get"])
    def results(self, request, pk=None):
        """Get results of all attempts for this quiz."""
        quiz = self.get_object()
        attempts = QuizAttempt.objects.filter(
            quiz=quiz, student=request.user, is_completed=True
        ).prefetch_related("answers")
        return Response(QuizResultSerializer(attempts, many=True).data)
