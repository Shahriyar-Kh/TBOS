import types

import pytest

from apps.core.utils.parse_and_save_aiken import parse_and_save_aiken
from apps.core.utils.video_durations import video_duration
from tests.factories import CourseFactory, VideoFactory


@pytest.mark.django_db
class TestCoreUtils:
    def test_video_duration_returns_single_course_h_m(self):
        course = CourseFactory()
        VideoFactory(course=course, lesson__section__course=course, duration_seconds=3600)
        VideoFactory(course=course, lesson__section__course=course, duration_seconds=600)

        result = video_duration(course)

        assert result == "1h 10m"

    def test_video_duration_returns_dict_for_multiple_courses(self):
        course_1 = CourseFactory()
        course_2 = CourseFactory()
        VideoFactory(course=course_1, lesson__section__course=course_1, duration_seconds=120)
        VideoFactory(course=course_2, lesson__section__course=course_2, duration_seconds=180)

        result = video_duration([course_1, course_2])

        assert isinstance(result, dict)
        assert result[course_1.id] == "2m"
        assert result[course_2.id] == "3m"

    def test_parse_and_save_aiken_raises_on_unfinished_question(self, tmp_path):
        file_path = tmp_path / "bad.aiken"
        file_path.write_text("What is Django?\nA. Framework\nB. Library\n", encoding="utf-8")

        with pytest.raises(ValueError, match="Unfinished question"):
            parse_and_save_aiken(str(file_path), quiz=object())

    def test_parse_and_save_aiken_can_parse_and_save_with_monkeypatched_models(self, tmp_path, monkeypatch):
        captured_questions = []
        captured_options = []

        class FakeQuestionManager:
            @staticmethod
            def create(**kwargs):
                captured_questions.append(kwargs)
                return types.SimpleNamespace(id="q1")

        class FakeOptionManager:
            @staticmethod
            def create(**kwargs):
                captured_options.append(kwargs)
                return types.SimpleNamespace(id="o1")

        class FakeQuestion:
            objects = FakeQuestionManager()

        class FakeOption:
            objects = FakeOptionManager()

        monkeypatch.setattr("apps.quiz.models.Question", FakeQuestion)
        monkeypatch.setattr("apps.quiz.models.Option", FakeOption)

        file_path = tmp_path / "ok.aiken"
        file_path.write_text(
            "What is Python?\nA. Language\nB. Database\nANSWER: A\n",
            encoding="utf-8",
        )

        parse_and_save_aiken(str(file_path), quiz="quiz-1")

        assert len(captured_questions) == 1
        assert captured_questions[0]["quiz"] == "quiz-1"
        assert len(captured_options) == 2
