import pytest

from apps.analytics.models import UserActivity
from apps.analytics.serializers import StudentAnalyticsSerializer, TrackActivitySerializer


@pytest.mark.django_db
class TestAnalyticsSerializers:
    def test_student_analytics_serializer_output(self):
        serializer = StudentAnalyticsSerializer(
            {
                "courses_enrolled": 1,
                "courses_completed": 1,
                "lessons_completed": 5,
                "quizzes_attempted": 2,
                "assignments_submitted": 1,
                "certificates_earned": 1,
                "learning_streak_days": 3,
                "learning_hours": 4.5,
                "average_quiz_score": 88.0,
            }
        )
        assert serializer.data["courses_enrolled"] == 1

    def test_track_activity_serializer_validates_activity_type(self):
        serializer = TrackActivitySerializer(data={"activity_type": UserActivity.ActivityType.LOGIN})
        assert serializer.is_valid(), serializer.errors
