import pytest

from apps.ai_tools.serializers import AIQuizGenerateRequestSerializer, AISuggestRequestSerializer


@pytest.mark.django_db
class TestAIToolsSerializers:
    def test_generate_quiz_request_serializer_valid(self):
        serializer = AIQuizGenerateRequestSerializer(
            data={
                "course_id": "11111111-1111-1111-1111-111111111111",
                "prompt": "Generate intro quiz",
                "num_questions": 10,
            }
        )
        assert serializer.is_valid(), serializer.errors

    def test_generate_quiz_request_serializer_rejects_large_question_count(self):
        serializer = AIQuizGenerateRequestSerializer(
            data={
                "course_id": "11111111-1111-1111-1111-111111111111",
                "prompt": "Generate intro quiz",
                "num_questions": 100,
            }
        )
        assert not serializer.is_valid()

    def test_ai_suggest_request_serializer_valid(self):
        serializer = AISuggestRequestSerializer(
            data={
                "suggestion_type": "lesson_outline",
                "input_text": "Build LMS lesson plan",
            }
        )
        assert serializer.is_valid(), serializer.errors
