from rest_framework import serializers

from apps.enrollments.models import Enrollment, LessonProgress
from apps.courses.serializers import CourseListSerializer


class EnrollmentSerializer(serializers.ModelSerializer):
    course_detail = CourseListSerializer(source="course", read_only=True)

    class Meta:
        model = Enrollment
        fields = [
            "id",
            "student",
            "course",
            "course_detail",
            "is_active",
            "completed_at",
            "progress_percent",
            "last_accessed_at",
            "created_at",
        ]
        read_only_fields = [
            "id",
            "student",
            "is_active",
            "completed_at",
            "progress_percent",
            "last_accessed_at",
            "created_at",
        ]


class EnrollmentCreateSerializer(serializers.Serializer):
    course_id = serializers.UUIDField()


class LessonProgressSerializer(serializers.ModelSerializer):
    lesson_title = serializers.CharField(source="lesson.title", read_only=True)

    class Meta:
        model = LessonProgress
        fields = [
            "id",
            "enrollment",
            "lesson",
            "lesson_title",
            "is_completed",
            "completed_at",
        ]
        read_only_fields = ["id", "enrollment", "completed_at"]


class MarkLessonCompleteSerializer(serializers.Serializer):
    lesson_id = serializers.UUIDField()
