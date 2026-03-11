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
    parent_category_id = serializers.UUIDField(
        source="parent_category.id", read_only=True, allow_null=True
    )

    class Meta:
        model = Category
        fields = ["id", "name", "icon", "slug", "description", "parent_category_id"]
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
            "rating_count",
            "total_enrollments",
            "duration_hours",
            "total_lessons",
            "created_at",
        ]


class CoursePublicSerializer(serializers.ModelSerializer):
    """Serializer for public API responses — excludes private/admin fields."""
    category = CategorySerializer(read_only=True)
    level = LevelSerializer(read_only=True)
    language = LanguageSerializer(read_only=True)
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
            "promo_video_url",
            "price",
            "effective_price",
            "is_free",
            "category",
            "level",
            "language",
            "instructor_name",
            "certificate_available",
            "average_rating",
            "rating_count",
            "total_enrollments",
            "duration_hours",
            "total_lessons",
            "published_at",
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
            "certificate_available",
            "category",
            "level",
            "language",
            "instructor_name",
            "instructor_id",
            "average_rating",
            "rating_count",
            "total_enrollments",
            "duration_hours",
            "total_lessons",
            "learning_outcomes",
            "requirements",
            "published_at",
            "created_at",
            "updated_at",
        ]


class CourseCreateSerializer(serializers.ModelSerializer):
    """Used when an instructor creates a new course."""
    category_id = serializers.UUIDField(write_only=True)
    level_id = serializers.UUIDField(write_only=True, required=False, allow_null=True)
    language_id = serializers.UUIDField(write_only=True, required=False, allow_null=True)

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
            "certificate_available",
            "category_id",
            "level_id",
            "language_id",
        ]

    def validate_title(self, value):
        if len(value.strip()) < 10:
            raise serializers.ValidationError(
                "Course title must be at least 10 characters long."
            )
        return value.strip()

    def validate_price(self, value):
        if value < 0:
            raise serializers.ValidationError("Price cannot be negative.")
        return value

    def validate_discount(self, value):
        if value < 0 or value > 100:
            raise serializers.ValidationError("Discount must be between 0 and 100.")
        return value

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


class CourseUpdateSerializer(serializers.ModelSerializer):
    """Used when an instructor or admin edits a course."""
    category_id = serializers.UUIDField(write_only=True, required=False, allow_null=True)
    level_id = serializers.UUIDField(write_only=True, required=False, allow_null=True)
    language_id = serializers.UUIDField(write_only=True, required=False, allow_null=True)

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
            "certificate_available",
            "duration_hours",
            "category_id",
            "level_id",
            "language_id",
        ]

    def validate_title(self, value):
        if value is not None and len(value.strip()) < 10:
            raise serializers.ValidationError(
                "Course title must be at least 10 characters long."
            )
        return value.strip() if value else value

    def validate_price(self, value):
        if value is not None and value < 0:
            raise serializers.ValidationError("Price cannot be negative.")
        return value

    def validate_discount(self, value):
        if value is not None and (value < 0 or value > 100):
            raise serializers.ValidationError("Discount must be between 0 and 100.")
        return value

    def validate_category_id(self, value):
        if value and not Category.objects.filter(id=value).exists():
            raise serializers.ValidationError("Category not found.")
        return value

    def update(self, instance, validated_data):
        category_id = validated_data.pop("category_id", None)
        if category_id:
            validated_data["category_id"] = category_id
        level_id = validated_data.pop("level_id", None)
        if level_id is not None:
            validated_data["level_id"] = level_id
        language_id = validated_data.pop("language_id", None)
        if language_id is not None:
            validated_data["language_id"] = language_id
        return super().update(instance, validated_data)


# Backward compatibility alias
CourseCreateUpdateSerializer = CourseCreateSerializer
