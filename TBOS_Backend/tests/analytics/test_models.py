import pytest

from apps.analytics.models import UserActivity
from tests.factories import CourseFactory, UserFactory


@pytest.mark.django_db
class TestAnalyticsModels:
    def test_course_analytics_string_representation(self):
        course = CourseFactory()
        snapshot = course.analytics_snapshots.create(total_students=10)
        assert course.title in str(snapshot)

    def test_user_activity_string_representation(self):
        user = UserFactory()
        activity = UserActivity.objects.create(user=user, activity_type=UserActivity.ActivityType.LOGIN)
        assert user.email in str(activity)
