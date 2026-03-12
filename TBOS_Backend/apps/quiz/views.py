from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated

from apps.core.exceptions import api_success, api_error
from apps.core.pagination import StandardPagination
from apps.core.permissions import IsAdminOrInstructor, IsAdmin, IsStudent
from apps.quiz.models import Option, Question, Quiz, StudentAnswer, QuizAttempt
from apps.quiz.services.quiz_service import QuizService
from apps.quiz.serializers import (
    OptionCreateSerializer,
    OptionSerializer,
    QuestionCreateSerializer,
    QuestionSerializer,
    QuizAttemptSerializer,
    QuizCreateSerializer,
    QuizDetailSerializer,
    QuizResultSerializer,
    QuizSerializer,
    QuestionStudentSerializer,
    QuizStudentDetailSerializer,
    QuizSubmitSerializer,
    SubmitAnswerSerializer,
)


# ──────────────────────────────────────────────
# Instructor / Admin
# ──────────────────────────────────────────────


class InstructorQuizViewSet(viewsets.ModelViewSet):
    """
    /api/v1/quiz/instructor/quizzes/
    Full CRUD for quizzes (instructor owns the course).
    """
    permission_classes = [IsAuthenticated, IsAdminOrInstructor]
    pagination_class = StandardPagination

    def get_serializer_class(self):
        if self.action == "retrieve":
            return QuizDetailSerializer
        if self.action in ("create", "update", "partial_update"):
            return QuizCreateSerializer
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

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            paginated = self.get_paginated_response(serializer.data)
            return api_success(data=paginated.data, message="Quizzes retrieved.")
        serializer = self.get_serializer(queryset, many=True)
        return api_success(data=serializer.data, message="Quizzes retrieved.")

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return api_success(data=serializer.data, message="Quiz retrieved.")

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return api_success(
            data=serializer.data,
            message="Quiz created successfully.",
            status_code=status.HTTP_201_CREATED,
        )

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return api_success(data=serializer.data, message="Quiz updated successfully.")

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.delete()
        return api_success(message="Quiz deleted successfully.", status_code=status.HTTP_200_OK)


class InstructorQuestionViewSet(viewsets.ModelViewSet):
    """
    /api/v1/quiz/instructor/questions/
    """
    permission_classes = [IsAuthenticated, IsAdminOrInstructor]

    def get_serializer_class(self):
        if self.action in ("create", "update", "partial_update"):
            return QuestionCreateSerializer
        return QuestionSerializer

    def get_queryset(self):
        user = self.request.user
        qs = Question.objects.select_related("quiz__course").prefetch_related("options")
        if user.role == "instructor":
            qs = qs.filter(quiz__course__instructor=user)
        quiz_id = self.request.query_params.get("quiz")
        if quiz_id:
            qs = qs.filter(quiz_id=quiz_id)
        return qs

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        return api_success(data=serializer.data, message="Questions retrieved.")

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return api_success(
            data=serializer.data,
            message="Question added successfully.",
            status_code=status.HTTP_201_CREATED,
        )

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.delete()
        return api_success(message="Question deleted successfully.")


class InstructorOptionViewSet(viewsets.ModelViewSet):
    """
    /api/v1/quiz/instructor/options/
    """
    permission_classes = [IsAuthenticated, IsAdminOrInstructor]

    def get_serializer_class(self):
        if self.action in ("create", "update", "partial_update"):
            return OptionCreateSerializer
        return OptionSerializer

    def get_queryset(self):
        qs = Option.objects.select_related("question__quiz__course")
        if self.request.user.role == "instructor":
            qs = qs.filter(question__quiz__course__instructor=self.request.user)
        question_id = self.request.query_params.get("question")
        if question_id:
            qs = qs.filter(question_id=question_id)
        return qs

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        return api_success(data=serializer.data, message="Options retrieved.")

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return api_success(
            data=serializer.data,
            message="Option added successfully.",
            status_code=status.HTTP_201_CREATED,
        )

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.delete()
        return api_success(message="Option deleted successfully.")


# ──────────────────────────────────────────────
# Admin
# ──────────────────────────────────────────────


class AdminQuizViewSet(viewsets.ModelViewSet):
    """
    /api/v1/quiz/admin/quizzes/
    Admin management of all quizzes.
    """
    serializer_class = QuizSerializer
    permission_classes = [IsAuthenticated, IsAdmin]
    pagination_class = StandardPagination

    def get_serializer_class(self):
        if self.action == "retrieve":
            return QuizDetailSerializer
        return QuizSerializer

    def get_queryset(self):
        return Quiz.objects.select_related("course", "lesson").prefetch_related(
            "questions__options"
        ).all()

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            paginated = self.get_paginated_response(serializer.data)
            return api_success(data=paginated.data, message="Quizzes retrieved.")
        serializer = self.get_serializer(queryset, many=True)
        return api_success(data=serializer.data, message="Quizzes retrieved.")

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.delete()
        return api_success(message="Quiz deleted successfully.")


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
            course_id__in=enrolled_courses, is_active=True
        )

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        return api_success(data=serializer.data, message="Quizzes retrieved.")

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = QuizStudentDetailSerializer(instance)
        return api_success(data=serializer.data, message="Quiz retrieved.")

    @action(detail=True, methods=["post"])
    def start(self, request, pk=None):
        """POST /api/v1/quiz/student/{id}/start/ — Start quiz attempt."""
        quiz = self.get_object()
        try:
            attempt, created = QuizService.start_attempt(quiz=quiz, student=request.user)
        except ValueError as exc:
            return api_error(
                errors={"detail": str(exc)},
                message=str(exc),
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        questions = QuizService.get_quiz_questions(quiz)
        return api_success(
            data={
                "attempt": QuizAttemptSerializer(attempt).data,
                "questions": QuestionStudentSerializer(questions, many=True).data,
            },
            message="Quiz attempt started." if created else "Resuming existing attempt.",
            status_code=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )

    @action(detail=True, methods=["get"], url_path="questions")
    def get_questions(self, request, pk=None):
        """Get questions for an active attempt (no correct answers shown)."""
        quiz = self.get_object()
        questions = QuizService.get_quiz_questions(quiz)
        return api_success(
            data=QuestionStudentSerializer(questions, many=True).data,
            message="Questions retrieved.",
        )

    @action(detail=True, methods=["post"], url_path="submit-answer")
    def submit_answer(self, request, pk=None):
        """Submit an answer for one question in an active attempt."""
        quiz = self.get_object()
        serializer = SubmitAnswerSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        attempt = QuizAttempt.objects.filter(
            quiz=quiz, student=request.user, status=QuizAttempt.Status.IN_PROGRESS
        ).first()
        if not attempt:
            return api_error(
                errors={"detail": "No active attempt found."},
                message="No active attempt found.",
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        try:
            answer = QuizService.submit_answer(
                attempt=attempt,
                question_id=serializer.validated_data["question_id"],
                option_id=serializer.validated_data["option_id"],
            )
        except ValueError as exc:
            return api_error(
                errors={"detail": str(exc)},
                message=str(exc),
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        return api_success(
            data={"submitted": True, "answer_id": str(answer.id)},
            message="Answer submitted.",
        )

    @action(detail=True, methods=["post"])
    def submit(self, request, pk=None):
        """POST /api/v1/quiz/student/{id}/submit/ — Submit quiz and calculate score."""
        quiz = self.get_object()
        attempt = QuizAttempt.objects.filter(
            quiz=quiz, student=request.user, status=QuizAttempt.Status.IN_PROGRESS
        ).first()
        if not attempt:
            return api_error(
                errors={"detail": "No active attempt found."},
                message="No active attempt found.",
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        try:
            attempt = QuizService.submit_quiz(attempt)
        except ValueError as exc:
            return api_error(
                errors={"detail": str(exc)},
                message=str(exc),
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        return api_success(
            data=QuizResultSerializer(attempt).data,
            message="Quiz submitted successfully.",
        )

    @action(detail=True, methods=["get"], url_path="result")
    def result(self, request, pk=None):
        """GET /api/v1/quiz/student/{id}/result/ — View results."""
        quiz = self.get_object()
        attempts = QuizService.get_quiz_results(quiz, request.user)
        if not attempts.exists():
            return api_error(
                errors={"detail": "No completed attempts found."},
                message="No completed attempts found.",
                status_code=status.HTTP_404_NOT_FOUND,
            )
        return api_success(
            data=QuizResultSerializer(attempts, many=True).data,
            message="Quiz results retrieved.",
        )
