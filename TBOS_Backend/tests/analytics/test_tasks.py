from unittest.mock import patch

import pytest

from apps.analytics.tasks import aggregate_platform_metrics_task, update_course_analytics, update_course_analytics_task


@pytest.mark.django_db
class TestAnalyticsTasks:
    @patch("apps.analytics.tasks.publish_admin_dashboard_update")
    @patch("apps.analytics.tasks.update_course_analytics_service")
    def test_update_course_analytics_task_publishes_count(self, mocked_update_service, mocked_publish):
        mocked_update_service.return_value = [object(), object()]

        result = update_course_analytics_task()

        assert result["updated_courses"] == 2
        mocked_publish.assert_called_once()

    @patch("apps.analytics.tasks.publish_admin_dashboard_update")
    @patch("apps.analytics.tasks.get_admin_dashboard")
    def test_aggregate_platform_metrics_task_returns_snapshot(self, mocked_get_dashboard, mocked_publish):
        mocked_get_dashboard.return_value = {
            "total_users": 10,
            "total_courses": 4,
            "total_revenue": 99.5,
        }

        result = aggregate_platform_metrics_task()

        assert result["total_users"] == 10
        assert result["total_courses"] == 4
        assert result["total_revenue"] == "99.5"
        mocked_publish.assert_called_once()

    @patch("apps.analytics.tasks.update_course_analytics_task")
    def test_update_course_analytics_alias_calls_primary_task(self, mocked_primary):
        mocked_primary.return_value = {"updated_courses": 1}

        result = update_course_analytics()

        assert result == {"updated_courses": 1}
