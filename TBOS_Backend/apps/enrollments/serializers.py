from rest_framework import serializers

from apps.enrollments.models import Enrollment, LessonProgress, VideoProgress
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
            "enrollment_status",
            "is_active",
            "progress_percentage",
            "completed_lessons_count",
            "total_lessons_count",
            "enrolled_at",
            "completed_at",
            "last_accessed_at",
            "created_at",
        ]
        read_only_fields = [
            "id",
            "student",
            "enrollment_status",
            "is_active",
            "progress_percentage",
            "completed_lessons_count",
            "total_lessons_count",
            "enrolled_at",
            "completed_at",
            "last_accessed_at",
            "created_at",
        ]


class EnrollmentDetailSerializer(serializers.ModelSerializer):
    """Detailed enrollment info with progress data."""

    course_detail = CourseListSerializer(source="course", read_only=True)
    student_email = serializers.EmailField(source="student.email", read_only=True)
    student_name = serializers.CharField(source="student.full_name", read_only=True)

    class Meta:
        model = Enrollment
        fields = [
            "id",
            "student",
            "student_email",
            "student_name",
            "course",
            "course_detail",
            "enrollment_status",
            "is_active",
            "progress_percentage",
            "completed_lessons_count",
            "total_lessons_count",
            "enrolled_at",
            "completed_at",
            "last_accessed_at",
            "created_at",
        ]


class EnrollmentCreateSerializer(serializers.Serializer):
    course_id = serializers.UUIDField()


class LessonProgressSerializer(serializers.ModelSerializer):
    lesson_title = serializers.CharField(source="lesson.title", read_only=True)
    lesson_id = serializers.UUIDField(source="lesson.id", read_only=True)

    class Meta:
        model = LessonProgress
        fields = [
            "id",
            "lesson_id",
            "lesson_title",
            "is_completed",
            "completed_at",
        ]
        read_only_fields = ["id", "completed_at"]


class MarkLessonCompleteSerializer(serializers.Serializer):
    lesson_id = serializers.UUIDField()


class VideoProgressSerializer(serializers.ModelSerializer):
    video_id = serializers.UUIDField(source="video.id", read_only=True)
    video_title = serializers.CharField(source="video.title", read_only=True)

    class Meta:
        model = VideoProgress
        fields = [
            "id",
            "video_id",
            "video_title",
            "watch_time_seconds",
            "last_position_seconds",
            "is_completed",
            "updated_at",
        ]
        read_only_fields = ["id", "is_completed", "updated_at"]


class VideoProgressUpdateSerializer(serializers.Serializer):
    video_id = serializers.UUIDField()
    watch_time_seconds = serializers.IntegerField(min_value=0)
    last_position_seconds = serializers.IntegerField(min_value=0)
