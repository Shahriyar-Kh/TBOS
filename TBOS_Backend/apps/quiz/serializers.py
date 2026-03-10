from rest_framework import serializers

from apps.quiz.models import Option, Question, Quiz, QuizAnswer, QuizAttempt


class OptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Option
        fields = ["id", "text", "is_correct", "order"]
        read_only_fields = ["id"]


class OptionStudentSerializer(serializers.ModelSerializer):
    """Hide is_correct from students."""
    class Meta:
        model = Option
        fields = ["id", "text", "order"]


class QuestionSerializer(serializers.ModelSerializer):
    options = OptionSerializer(many=True, read_only=True)

    class Meta:
        model = Question
        fields = ["id", "quiz", "text", "order", "points", "options"]
        read_only_fields = ["id"]


class QuestionStudentSerializer(serializers.ModelSerializer):
    """Hide correct answers from students."""
    options = OptionStudentSerializer(many=True, read_only=True)

    class Meta:
        model = Question
        fields = ["id", "text", "order", "points", "options"]


class QuizSerializer(serializers.ModelSerializer):
    question_count = serializers.SerializerMethodField()

    class Meta:
        model = Quiz
        fields = [
            "id",
            "course",
            "lesson",
            "title",
            "description",
            "time_limit_minutes",
            "max_attempts",
            "pass_percentage",
            "is_published",
            "order",
            "question_count",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def get_question_count(self, obj):
        return obj.questions.count()


class QuizDetailSerializer(QuizSerializer):
    questions = QuestionSerializer(many=True, read_only=True)

    class Meta(QuizSerializer.Meta):
        fields = QuizSerializer.Meta.fields + ["questions"]


class QuizStartSerializer(serializers.Serializer):
    quiz_id = serializers.UUIDField()


class SubmitAnswerSerializer(serializers.Serializer):
    question_id = serializers.UUIDField()
    option_id = serializers.UUIDField()


class QuizAttemptSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuizAttempt
        fields = [
            "id",
            "quiz",
            "student",
            "score",
            "total_points",
            "percentage",
            "passed",
            "started_at",
            "completed_at",
            "is_completed",
        ]


class QuizAnswerSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuizAnswer
        fields = ["id", "question", "selected_option", "is_correct"]


class QuizResultSerializer(serializers.ModelSerializer):
    answers = QuizAnswerSerializer(many=True, read_only=True)
    quiz_title = serializers.CharField(source="quiz.title", read_only=True)

    class Meta:
        model = QuizAttempt
        fields = [
            "id",
            "quiz",
            "quiz_title",
            "score",
            "total_points",
            "percentage",
            "passed",
            "started_at",
            "completed_at",
            "answers",
        ]
