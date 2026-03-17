from rest_framework import status
from drf_spectacular.utils import extend_schema
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.api_docs import AUTH_GUIDE, ROLE_ACCESS_GUIDE, standard_error_responses, success_response
from apps.core.exceptions import api_success, api_error
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

    @extend_schema(
        tags=["Quiz"],
        summary="Queue AI quiz generation",
        description=f"Create an asynchronous AI quiz generation job for a course.\n\n{AUTH_GUIDE}\n\n{ROLE_ACCESS_GUIDE}",
        request=AIQuizGenerateRequestSerializer,
        responses={202: success_response("AIQuizGenerateResponse", AIQuizGenerationSerializer), **standard_error_responses(400, 401, 403, 500)},
    )
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

        return api_success(
            data=AIQuizGenerationSerializer(job).data,
            message="Quiz generation job queued.",
            status_code=status.HTTP_202_ACCEPTED,
        )


class AIQuizStatusView(APIView):
    """
    GET /api/v1/ai/generate-quiz/{id}/status/
    Check status of an AI quiz generation job.
    """
    permission_classes = [IsAuthenticated, IsAdminOrInstructor]

    @extend_schema(
        tags=["Quiz"],
        summary="Get AI quiz generation status",
        responses={200: success_response("AIQuizStatusResponse", AIQuizGenerationSerializer), **standard_error_responses(401, 403, 404, 500)},
    )
    def get(self, request, pk):
        try:
            job = AIQuizGeneration.objects.get(id=pk, initiated_by=request.user)
        except AIQuizGeneration.DoesNotExist:
            return api_error(message="Job not found.", status_code=status.HTTP_404_NOT_FOUND)
        return api_success(data=AIQuizGenerationSerializer(job).data, message="Job status retrieved.")


class AISuggestView(APIView):
    """
    POST /api/v1/ai/suggest/
    Get AI-powered content suggestions.
    """
    permission_classes = [IsAuthenticated, IsAdminOrInstructor]

    @extend_schema(
        tags=["Analytics"],
        summary="Queue AI content suggestion",
        request=AISuggestRequestSerializer,
        responses={202: success_response("AISuggestResponse", AIContentSuggestionSerializer), **standard_error_responses(400, 401, 403, 500)},
    )
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

        return api_success(
            data=AIContentSuggestionSerializer(suggestion).data,
            message="Content suggestion job queued.",
            status_code=status.HTTP_202_ACCEPTED,
        )


class AISuggestionHistoryView(APIView):
    """
    GET /api/v1/ai/suggestions/
    List past AI suggestions for the current user.
    """
    permission_classes = [IsAuthenticated, IsAdminOrInstructor]

    @extend_schema(
        tags=["Analytics"],
        summary="List AI suggestion history",
        responses={200: success_response("AISuggestionHistoryResponse", AIContentSuggestionSerializer, many=True), **standard_error_responses(401, 403, 500)},
    )
    def get(self, request):
        suggestions = AIContentSuggestion.objects.filter(
            initiated_by=request.user
        ).order_by("-created_at")[:50]
        return api_success(
            data=AIContentSuggestionSerializer(suggestions, many=True).data,
            message="Suggestion history retrieved.",
        )
