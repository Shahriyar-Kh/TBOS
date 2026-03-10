from rest_framework import serializers

from apps.ai_tools.models import AIContentSuggestion, AIQuizGeneration


class AIQuizGenerationSerializer(serializers.ModelSerializer):
    class Meta:
        model = AIQuizGeneration
        fields = [
            "id",
            "course",
            "quiz",
            "prompt",
            "num_questions",
            "status",
            "error_message",
            "initiated_by",
            "created_at",
        ]
        read_only_fields = [
            "id",
            "quiz",
            "status",
            "error_message",
            "initiated_by",
            "created_at",
        ]


class AIQuizGenerateRequestSerializer(serializers.Serializer):
    course_id = serializers.UUIDField()
    prompt = serializers.CharField()
    num_questions = serializers.IntegerField(min_value=1, max_value=50, default=10)


class AIContentSuggestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = AIContentSuggestion
        fields = [
            "id",
            "suggestion_type",
            "input_text",
            "output_text",
            "course",
            "initiated_by",
            "created_at",
        ]
        read_only_fields = ["id", "output_text", "initiated_by", "created_at"]


class AISuggestRequestSerializer(serializers.Serializer):
    suggestion_type = serializers.ChoiceField(
        choices=AIContentSuggestion.SuggestionType.choices
    )
    input_text = serializers.CharField()
    course_id = serializers.UUIDField(required=False)
