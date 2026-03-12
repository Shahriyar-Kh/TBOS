from rest_framework import serializers

from apps.quiz.models import Option, Question, Quiz, StudentAnswer, QuizAttempt


# ──────────────────────────────────────────────
# Instructor serializers (CRUD)
# ──────────────────────────────────────────────


class OptionCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Option
        fields = ["id", "question", "option_text", "is_correct", "order"]
        read_only_fields = ["id"]


class OptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Option
        fields = ["id", "option_text", "is_correct", "order"]
        read_only_fields = ["id"]


class OptionStudentSerializer(serializers.ModelSerializer):
    """Hide is_correct from students."""
    class Meta:
        model = Option
        fields = ["id", "option_text", "order"]


class QuestionCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Question
        fields = ["id", "quiz", "question_text", "question_type", "points", "order", "explanation"]
        read_only_fields = ["id"]


class QuestionSerializer(serializers.ModelSerializer):
    options = OptionSerializer(many=True, read_only=True)

    class Meta:
        model = Question
        fields = ["id", "quiz", "question_text", "question_type", "order", "points", "explanation", "options"]
        read_only_fields = ["id"]


class QuestionStudentSerializer(serializers.ModelSerializer):
    """Hide correct answers and explanations from students."""
    options = OptionStudentSerializer(many=True, read_only=True)

    class Meta:
        model = Question
        fields = ["id", "question_text", "order", "points", "options"]


# ──────────────────────────────────────────────
# Quiz serializers
# ──────────────────────────────────────────────


class QuizCreateSerializer(serializers.ModelSerializer):
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
            "passing_score",
            "shuffle_questions",
            "shuffle_options",
        ]
        read_only_fields = ["id"]


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
            "passing_score",
            "shuffle_questions",
            "shuffle_options",
            "is_active",
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


class QuizStudentDetailSerializer(serializers.ModelSerializer):
    """Quiz detail without correct answers — safe for students."""
    questions = QuestionStudentSerializer(many=True, read_only=True)
    question_count = serializers.SerializerMethodField()

    class Meta:
        model = Quiz
        fields = [
            "id",
            "title",
            "description",
            "time_limit_minutes",
            "max_attempts",
            "passing_score",
            "question_count",
            "questions",
        ]

    def get_question_count(self, obj):
        return obj.questions.count()


# ──────────────────────────────────────────────
# Attempt serializers
# ──────────────────────────────────────────────


class QuizStartSerializer(serializers.Serializer):
    quiz_id = serializers.UUIDField()


class SubmitAnswerSerializer(serializers.Serializer):
    question_id = serializers.UUIDField()
    option_id = serializers.UUIDField()


class QuizSubmitSerializer(serializers.Serializer):
    """Bulk submit all answers at once."""
    answers = SubmitAnswerSerializer(many=True)


class QuizAttemptSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuizAttempt
        fields = [
            "id",
            "quiz",
            "student",
            "attempt_number",
            "score",
            "total_points",
            "total_questions",
            "correct_answers",
            "percentage",
            "passed",
            "start_time",
            "end_time",
            "status",
        ]


class StudentAnswerSerializer(serializers.ModelSerializer):
    class Meta:
        model = StudentAnswer
        fields = ["id", "question", "selected_option", "is_correct"]


class QuizResultSerializer(serializers.ModelSerializer):
    answers = StudentAnswerSerializer(many=True, read_only=True)
    quiz_title = serializers.CharField(source="quiz.title", read_only=True)

    class Meta:
        model = QuizAttempt
        fields = [
            "id",
            "quiz",
            "quiz_title",
            "attempt_number",
            "score",
            "total_points",
            "total_questions",
            "correct_answers",
            "percentage",
            "passed",
            "start_time",
            "end_time",
            "status",
            "answers",
        ]
