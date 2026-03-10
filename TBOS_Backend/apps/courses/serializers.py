from rest_framework import serializers

from apps.courses.models import (
    Category,
    Course,
    Language,
    LearningOutcome,
    Level,
    Requirement,
)


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "name", "icon", "slug"]
        read_only_fields = ["id", "slug"]


class LevelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Level
        fields = ["id", "name"]
        read_only_fields = ["id"]


class LanguageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Language
        fields = ["id", "name"]
        read_only_fields = ["id"]


class LearningOutcomeSerializer(serializers.ModelSerializer):
    class Meta:
        model = LearningOutcome
        fields = ["id", "text", "order"]
        read_only_fields = ["id"]


class RequirementSerializer(serializers.ModelSerializer):
    class Meta:
        model = Requirement
        fields = ["id", "text", "order"]
        read_only_fields = ["id"]


class CourseListSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    level = LevelSerializer(read_only=True)
    instructor_name = serializers.CharField(
        source="instructor.full_name", read_only=True
    )
    effective_price = serializers.DecimalField(
        max_digits=10, decimal_places=2, read_only=True
    )

    class Meta:
        model = Course
        fields = [
            "id",
            "title",
            "slug",
            "subtitle",
            "featured_image",
            "price",
            "discount",
            "effective_price",
            "is_free",
            "status",
            "category",
            "level",
            "instructor_name",
            "average_rating",
            "total_enrollments",
            "duration_hours",
            "total_lessons",
            "created_at",
        ]


class CourseDetailSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    level = LevelSerializer(read_only=True)
    language = LanguageSerializer(read_only=True)
    learning_outcomes = LearningOutcomeSerializer(many=True, read_only=True)
    requirements = RequirementSerializer(many=True, read_only=True)
    instructor_name = serializers.CharField(
        source="instructor.full_name", read_only=True
    )
    instructor_id = serializers.UUIDField(
        source="instructor.id", read_only=True
    )
    effective_price = serializers.DecimalField(
        max_digits=10, decimal_places=2, read_only=True
    )

    class Meta:
        model = Course
        fields = [
            "id",
            "title",
            "slug",
            "subtitle",
            "description",
            "featured_image",
            "promo_video_url",
            "price",
            "discount",
            "effective_price",
            "is_free",
            "status",
            "category",
            "level",
            "language",
            "instructor_name",
            "instructor_id",
            "average_rating",
            "total_enrollments",
            "duration_hours",
            "total_lessons",
            "learning_outcomes",
            "requirements",
            "created_at",
            "updated_at",
        ]


class CourseCreateUpdateSerializer(serializers.ModelSerializer):
    category_id = serializers.UUIDField(write_only=True)
    level_id = serializers.UUIDField(write_only=True, required=False)
    language_id = serializers.UUIDField(write_only=True, required=False)

    class Meta:
        model = Course
        fields = [
            "title",
            "subtitle",
            "description",
            "featured_image",
            "promo_video_url",
            "price",
            "discount",
            "is_free",
            "status",
            "category_id",
            "level_id",
            "language_id",
        ]

    def validate_category_id(self, value):
        if not Category.objects.filter(id=value).exists():
            raise serializers.ValidationError("Category not found.")
        return value

    def create(self, validated_data):
        validated_data["instructor"] = self.context["request"].user
        category_id = validated_data.pop("category_id")
        validated_data["category_id"] = category_id
        level_id = validated_data.pop("level_id", None)
        if level_id:
            validated_data["level_id"] = level_id
        language_id = validated_data.pop("language_id", None)
        if language_id:
            validated_data["language_id"] = language_id
        return super().create(validated_data)
