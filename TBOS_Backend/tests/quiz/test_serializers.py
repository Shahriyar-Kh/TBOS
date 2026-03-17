import pytest

from apps.quiz.serializers import OptionStudentSerializer, QuizSubmitSerializer
from tests.factories import OptionFactory


@pytest.mark.django_db
class TestQuizSerializers:
    def test_option_student_serializer_hides_correct_answer_flag(self):
        option = OptionFactory(is_correct=True)
        data = OptionStudentSerializer(option).data
        assert "is_correct" not in data

    def test_quiz_submit_serializer_validates_answers_list(self):
        serializer = QuizSubmitSerializer(
            data={
                "answers": [
                    {
                        "question_id": "4d715530-e218-4f71-aea8-b03f2f1494c5",
                        "option_id": "e84303e6-562b-4f3f-b1f4-22ebc9f220ea",
                    }
                ]
            }
        )
        assert serializer.is_valid(), serializer.errors
