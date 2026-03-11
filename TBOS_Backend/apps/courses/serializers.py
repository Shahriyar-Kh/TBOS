from decimal import Decimal

from rest_framework import serializers

from apps.courses.models import (
    Category,
    Course,
    CourseCategory,
    CourseLanguage,
    CourseLevel,
    Language,
    LearningOutcome,
    Level,
    Requirement,
)


# ──────────────────────────────────────────────────────────────
# Lookup serializers
# ──────────────────────────────────────────────────────────────

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "name", "icon", "slug"]
        read_only_fields = ["id", "slug"]


class CourseCategorySerializer(serializers.ModelSerializer):
    parent_id = serializers.UUIDField(source="parent.id", read_only=True, allow_null=True)

    class Meta:
        model = CourseCategory
        fields = ["id", "name", "slug", "icon", "description", "parent_id", "created_at"]
        read_only_fields = ["id", "slug", "created_at"]


class LevelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Level
        fields = ["id", "name"]
        read_only_fields = ["id"]


class CourseLevelSerializer(serializers.ModelSerializer):
    class Meta:
        model = CourseLevel
        fields = ["id", "name"]
        read_only_fields = ["id"]


class LanguageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Language
        fields = ["id", "name"]
        read_only_fields = ["id"]


class CourseLanguageSerializer(serializers.ModelSerializer):
    class Meta:
        model = CourseLanguage
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


# ──────────────────────────────────────────────────────────────
# Course list serializer (public-facing, minimal fields)
# ──────────────────────────────────────────────────────────────

class CourseListSerializer(serializers.ModelSerializer):
    """Used for paginated course listing – minimal payload."""

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
            "thumbnail",
            "featured_image",
            "price",
            "discount_price",
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


# ──────────────────────────────────────────────────────────────
# Course detail serializer (full metadata)
# ──────────────────────────────────────────────────────────────

class CourseDetailSerializer(serializers.ModelSerializer):
    """Full course detail including outcomes, requirements, instructor."""

    category = CategorySerializer(read_only=True)
    level = LevelSerializer(read_only=True)
    language = LanguageSerializer(read_only=True)
    learning_outcomes = LearningOutcomeSerializer(many=True, read_only=True)
    requirements = RequirementSerializer(many=True, read_only=True)
    instructor_name = serializers.CharField(
        source="instructor.full_name", read_only=True
    )
    instructor_id = serializers.UUIDField(source="instructor.id", read_only=True)
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
            "thumbnail",
            "featured_image",
            "promo_video_url",
            "price",
            "discount_price",
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


# ──────────────────────────────────────────────────────────────
# Public serializer (used for unauthenticated responses)
# Excludes private/admin-only fields like status, earnings info
# ──────────────────────────────────────────────────────────────

class CoursePublicSerializer(serializers.ModelSerializer):
    """Stripped-down public representation excluding internal fields."""

    category = CategorySerializer(read_only=True)
    level = LevelSerializer(read_only=True)
    language = LanguageSerializer(read_only=True)
    learning_outcomes = LearningOutcomeSerializer(many=True, read_only=True)
    requirements = RequirementSerializer(many=True, read_only=True)
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
            "description",
            "thumbnail",
            "promo_video_url",
            "price",
            "effective_price",
            "is_free",
            "certificate_available",
            "category",
            "level",
            "language",
            "instructor_name",
            "average_rating",
            "rating_count",
            "total_enrollments",
            "duration_hours",
            "total_lessons",
            "learning_outcomes",
            "requirements",
        ]


# ──────────────────────────────────────────────────────────────
# Write serializers
# ──────────────────────────────────────────────────────────────

class CourseCreateSerializer(serializers.ModelSerializer):
    """Used by instructors to create a new course."""

    category_id = serializers.UUIDField(write_only=True)
    level_id = serializers.UUIDField(write_only=True, required=False, allow_null=True)
    language_id = serializers.UUIDField(write_only=True, required=False, allow_null=True)

    class Meta:
        model = Course
        fields = [
            "title",
            "subtitle",
            "description",
            "thumbnail",
            "promo_video_url",
            "price",
            "discount_price",
            "is_free",
            "certificate_available",
            "category_id",
            "level_id",
            "language_id",
        ]

    def validate_title(self, value):
        if len(value.strip()) < 5:
            raise serializers.ValidationError(
                "Title must be at least 5 characters long."
            )
        return value.strip()

    def validate_price(self, value):
        if value < Decimal("0"):
            raise serializers.ValidationError("Price cannot be negative.")
        return value

    def validate_discount_price(self, value):
        if value < Decimal("0"):
            raise serializers.ValidationError("Discount price cannot be negative.")
        return value

    def validate(self, attrs):
        price = attrs.get("price", Decimal("0"))
        discount_price = attrs.get("discount_price", Decimal("0"))
        if discount_price and discount_price >= price and price > Decimal("0"):
            raise serializers.ValidationError(
                {"discount_price": "Discount price must be less than the original price."}
            )
        return attrs

    def validate_category_id(self, value):
        if not Category.objects.filter(id=value).exists():
            raise serializers.ValidationError("Category not found.")
        return value


class CourseUpdateSerializer(serializers.ModelSerializer):
    """Used by instructors/admins to edit an existing course."""

    category_id = serializers.UUIDField(write_only=True, required=False, allow_null=True)
    level_id = serializers.UUIDField(write_only=True, required=False, allow_null=True)
    language_id = serializers.UUIDField(write_only=True, required=False, allow_null=True)

    class Meta:
        model = Course
        fields = [
            "title",
            "subtitle",
            "description",
            "thumbnail",
            "featured_image",
            "promo_video_url",
            "price",
            "discount_price",
            "discount",
            "is_free",
            "certificate_available",
            "duration_hours",
            "category_id",
            "level_id",
            "language_id",
        ]

    def validate_title(self, value):
        if len(value.strip()) < 5:
            raise serializers.ValidationError(
                "Title must be at least 5 characters long."
            )
        return value.strip()

    def validate_price(self, value):
        if value < Decimal("0"):
            raise serializers.ValidationError("Price cannot be negative.")
        return value

    def validate_discount_price(self, value):
        if value < Decimal("0"):
            raise serializers.ValidationError("Discount price cannot be negative.")
        return value

    def validate(self, attrs):
        # When updating, merge with existing values for cross-field validation
        instance = getattr(self, "instance", None)
        price = attrs.get("price", instance.price if instance else Decimal("0"))
        discount_price = attrs.get(
            "discount_price",
            instance.discount_price if instance else Decimal("0"),
        )
        if discount_price and discount_price >= price and price > Decimal("0"):
            raise serializers.ValidationError(
                {"discount_price": "Discount price must be less than the original price."}
            )
        return attrs

    def validate_category_id(self, value):
        if value and not Category.objects.filter(id=value).exists():
            raise serializers.ValidationError("Category not found.")
        return value


# Keep backward-compatible alias
CourseCreateUpdateSerializer = CourseUpdateSerializer
