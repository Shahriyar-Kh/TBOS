from rest_framework import serializers

from apps.lessons.models import Lesson


class LessonSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lesson
        fields = [
            "id",
            "course",
            "title",
            "description",
            "order",
            "is_published",
            "duration_minutes",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class LessonListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing lessons inside a course."""
    video_count = serializers.IntegerField(read_only=True, default=0)

    class Meta:
        model = Lesson
        fields = [
            "id",
            "title",
            "order",
            "is_published",
            "duration_minutes",
            "video_count",
        ]
