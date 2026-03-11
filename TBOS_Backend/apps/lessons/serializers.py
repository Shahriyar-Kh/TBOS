from rest_framework import serializers

from apps.lessons.models import CourseSection, Lesson


# ──────────────────────────────────────────────────────────────
# Lesson serializers
# ──────────────────────────────────────────────────────────────

class LessonCreateSerializer(serializers.ModelSerializer):
    """Used by instructors to create a lesson within a section."""

    class Meta:
        model = Lesson
        fields = [
            "id",
            "section",
            "title",
            "description",
            "lesson_type",
            "order",
            "is_preview",
            "duration_seconds",
            "article_content",
        ]
        read_only_fields = ["id"]

    def validate_title(self, value):
        if len(value.strip()) < 3:
            raise serializers.ValidationError(
                "Lesson title must be at least 3 characters long."
            )
        return value.strip()

    def validate_order(self, value):
        if value < 0:
            raise serializers.ValidationError("Order value must be a positive integer.")
        return value


class LessonUpdateSerializer(serializers.ModelSerializer):
    """Used by instructors to update an existing lesson."""

    class Meta:
        model = Lesson
        fields = [
            "title",
            "description",
            "lesson_type",
            "order",
            "is_preview",
            "duration_seconds",
            "article_content",
        ]

    def validate_title(self, value):
        if len(value.strip()) < 3:
            raise serializers.ValidationError(
                "Lesson title must be at least 3 characters long."
            )
        return value.strip()

    def validate_order(self, value):
        if value < 0:
            raise serializers.ValidationError("Order value must be a positive integer.")
        return value


class LessonDetailSerializer(serializers.ModelSerializer):
    """Full lesson metadata returned to clients."""

    section_id = serializers.UUIDField(source="section.id", read_only=True)

    class Meta:
        model = Lesson
        fields = [
            "id",
            "section_id",
            "title",
            "description",
            "lesson_type",
            "order",
            "is_preview",
            "duration_seconds",
            "article_content",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "section_id", "created_at", "updated_at"]


# ──────────────────────────────────────────────────────────────
# Section serializers
# ──────────────────────────────────────────────────────────────

class CourseSectionCreateSerializer(serializers.ModelSerializer):
    """Used by instructors to create a section within a course."""

    class Meta:
        model = CourseSection
        fields = [
            "id",
            "course",
            "title",
            "description",
            "order",
        ]
        read_only_fields = ["id"]

    def validate_order(self, value):
        if value < 0:
            raise serializers.ValidationError("Order value must be a positive integer.")
        return value


class CourseSectionUpdateSerializer(serializers.ModelSerializer):
    """Used by instructors to update an existing section."""

    class Meta:
        model = CourseSection
        fields = ["title", "description", "order"]

    def validate_order(self, value):
        if value < 0:
            raise serializers.ValidationError("Order value must be a positive integer.")
        return value


class CourseSectionDetailSerializer(serializers.ModelSerializer):
    """Section metadata plus nested lessons."""

    lessons = LessonDetailSerializer(many=True, read_only=True)

    class Meta:
        model = CourseSection
        fields = [
            "id",
            "course",
            "title",
            "description",
            "order",
            "lessons",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "course", "created_at", "updated_at"]


# ──────────────────────────────────────────────────────────────
# Curriculum serializer
# ──────────────────────────────────────────────────────────────

class CourseCurriculumSerializer(serializers.Serializer):
    """Full course curriculum: course metadata + sections + lessons."""

    course_id = serializers.UUIDField(read_only=True)
    title = serializers.CharField(read_only=True)
    slug = serializers.SlugField(read_only=True)
    sections = CourseSectionDetailSerializer(many=True, read_only=True)


# ──────────────────────────────────────────────────────────────
# Legacy serializers (kept for backward compatibility)
# ──────────────────────────────────────────────────────────────

class LessonSerializer(LessonDetailSerializer):
    """Alias kept for backward compatibility."""
    pass


class LessonListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing lessons."""

    class Meta:
        model = Lesson
        fields = [
            "id",
            "title",
            "order",
            "lesson_type",
            "is_preview",
            "duration_seconds",
        ]
