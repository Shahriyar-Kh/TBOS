from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.permissions import IsAdminOrInstructor
from apps.ai_tools.models import AIContentSuggestion, AIQuizGeneration
from apps.ai_tools.serializers import (
    AIContentSuggestionSerializer,
    AIQuizGenerateRequestSerializer,
    AIQuizGenerationSerializer,
    AISuggestRequestSerializer,
)
from apps.ai_tools.tasks import generate_ai_quiz, generate_ai_content_suggestion


class AIQuizGenerateView(APIView):
    """
    POST /api/v1/ai/generate-quiz/
    Queue an AI quiz generation job.
    """
    permission_classes = [IsAuthenticated, IsAdminOrInstructor]

    def post(self, request):
        serializer = AIQuizGenerateRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        job = AIQuizGeneration.objects.create(
            course_id=data["course_id"],
            prompt=data["prompt"],
            num_questions=data["num_questions"],
            initiated_by=request.user,
        )
        generate_ai_quiz.delay(str(job.id))

        return Response(
            AIQuizGenerationSerializer(job).data,
            status=status.HTTP_202_ACCEPTED,
        )


class AIQuizStatusView(APIView):
    """
    GET /api/v1/ai/generate-quiz/{id}/status/
    Check status of an AI quiz generation job.
    """
    permission_classes = [IsAuthenticated, IsAdminOrInstructor]

    def get(self, request, pk):
        try:
            job = AIQuizGeneration.objects.get(id=pk, initiated_by=request.user)
        except AIQuizGeneration.DoesNotExist:
            return Response(
                {"detail": "Job not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response(AIQuizGenerationSerializer(job).data)


class AISuggestView(APIView):
    """
    POST /api/v1/ai/suggest/
    Get AI-powered content suggestions.
    """
    permission_classes = [IsAuthenticated, IsAdminOrInstructor]

    def post(self, request):
        serializer = AISuggestRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        suggestion = AIContentSuggestion.objects.create(
            initiated_by=request.user,
            suggestion_type=data["suggestion_type"],
            input_text=data["input_text"],
            course_id=data.get("course_id"),
        )
        generate_ai_content_suggestion.delay(str(suggestion.id))

        return Response(
            AIContentSuggestionSerializer(suggestion).data,
            status=status.HTTP_202_ACCEPTED,
        )


class AISuggestionHistoryView(APIView):
    """
    GET /api/v1/ai/suggestions/
    List past AI suggestions for the current user.
    """
    permission_classes = [IsAuthenticated, IsAdminOrInstructor]

    def get(self, request):
        suggestions = AIContentSuggestion.objects.filter(
            initiated_by=request.user
        ).order_by("-created_at")[:50]
        return Response(
            AIContentSuggestionSerializer(suggestions, many=True).data
        )
