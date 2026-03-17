from rest_framework import serializers

from apps.analytics.models import CourseAnalytics, UserActivity


class CourseAnalyticsSerializer(serializers.ModelSerializer):
    course_id = serializers.UUIDField(source="course.id", read_only=True)

    class Meta:
        model = CourseAnalytics
        fields = [
            "course_id",
            "total_students",
            "average_progress",
            "rating_average",
            "total_revenue",
        ]


class StudentAnalyticsSerializer(serializers.Serializer):
    courses_enrolled = serializers.IntegerField()
    courses_completed = serializers.IntegerField()
    lessons_completed = serializers.IntegerField()
    quizzes_attempted = serializers.IntegerField()
    assignments_submitted = serializers.IntegerField()
    certificates_earned = serializers.IntegerField()
    learning_streak_days = serializers.IntegerField()
    learning_hours = serializers.FloatField()
    average_quiz_score = serializers.FloatField()


class InstructorAnalyticsSerializer(serializers.Serializer):
    total_courses = serializers.IntegerField()
    total_students = serializers.IntegerField()
    total_revenue = serializers.DecimalField(max_digits=14, decimal_places=2)
    average_rating = serializers.FloatField()
    course_completion_rate = serializers.FloatField()
    lesson_completion_rate = serializers.FloatField()
    quiz_performance = serializers.FloatField()
    assignment_submissions = serializers.IntegerField()


class AdminAnalyticsSerializer(serializers.Serializer):
    total_users = serializers.IntegerField()
    total_students = serializers.IntegerField()
    total_instructors = serializers.IntegerField()
    total_courses = serializers.IntegerField()
    total_enrollments = serializers.IntegerField()
    total_revenue = serializers.DecimalField(max_digits=14, decimal_places=2)
    course_completion_rate = serializers.FloatField()
    average_platform_rating = serializers.FloatField()


class UserActivitySerializer(serializers.ModelSerializer):
    class Meta:
        model = UserActivity
        fields = [
            "id",
            "user",
            "activity_type",
            "reference_id",
            "timestamp",
        ]
        read_only_fields = ["id", "timestamp"]


class TrackActivitySerializer(serializers.Serializer):
    activity_type = serializers.ChoiceField(choices=UserActivity.ActivityType.choices)
    reference_id = serializers.UUIDField(required=False, allow_null=True)


class RevenueAnalyticsSerializer(serializers.Serializer):
    start_date = serializers.DateField(required=False, allow_null=True)
    end_date = serializers.DateField(required=False, allow_null=True)
    total_revenue = serializers.DecimalField(max_digits=14, decimal_places=2)
    total_orders = serializers.IntegerField()
    average_order_value = serializers.DecimalField(max_digits=14, decimal_places=2)
