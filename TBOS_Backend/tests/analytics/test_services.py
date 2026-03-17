import pytest

from apps.analytics.models import UserActivity
from apps.analytics.services.analytics_service import AnalyticsService
from tests.factories import EnrollmentFactory, UserFactory


@pytest.mark.django_db
class TestAnalyticsServices:
    def test_calculate_student_progress_returns_required_keys(self):
        student = UserFactory()
        EnrollmentFactory(student=student)

        payload = AnalyticsService.calculate_student_progress(student)

        assert "courses_enrolled" in payload
        assert "average_quiz_score" in payload

    def test_record_user_activity_creates_activity(self):
        user = UserFactory()

        activity = AnalyticsService.record_user_activity(
            user=user,
            activity_type=UserActivity.ActivityType.LOGIN,
        )

        assert activity.user == user
        assert UserActivity.objects.filter(id=activity.id).exists()
