from rest_framework import serializers

from apps.analytics.models import CourseAnalytics, UserActivity


class CourseAnalyticsSerializer(serializers.ModelSerializer):
    course_title = serializers.CharField(source="course.title", read_only=True)

    class Meta:
        model = CourseAnalytics
        fields = [
            "id",
            "course",
            "course_title",
            "total_views",
            "total_watch_time_seconds",
            "total_completions",
            "avg_completion_percent",
            "total_revenue",
            "snapshot_date",
        ]


class UserActivitySerializer(serializers.ModelSerializer):
    class Meta:
        model = UserActivity
        fields = [
            "id",
            "user",
            "event_type",
            "course",
            "video",
            "metadata",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]


class TrackActivitySerializer(serializers.Serializer):
    event_type = serializers.ChoiceField(choices=UserActivity.EventType.choices)
    course_id = serializers.UUIDField(required=False)
    video_id = serializers.UUIDField(required=False)
    metadata = serializers.DictField(required=False, default=dict)


class PlatformStatsSerializer(serializers.Serializer):
    total_users = serializers.IntegerField()
    total_students = serializers.IntegerField()
    total_instructors = serializers.IntegerField()
    total_courses = serializers.IntegerField()
    total_enrollments = serializers.IntegerField()
    total_revenue = serializers.DecimalField(max_digits=14, decimal_places=2)
