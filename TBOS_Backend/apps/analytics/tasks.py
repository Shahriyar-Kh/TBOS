from celery import shared_task

from apps.analytics.services.realtime_service import publish_admin_dashboard_update
from apps.analytics.services.analytics_service import (
    get_admin_dashboard,
    update_course_analytics as update_course_analytics_service,
)


@shared_task
def update_course_analytics_task():
    """Periodic task to refresh per-course analytics snapshots."""
    updated = update_course_analytics_service()
    publish_admin_dashboard_update({"updated_courses": len(updated), "source": "celery"})
    return {"updated_courses": len(updated)}


@shared_task
def aggregate_platform_metrics_task():
    """Periodic task to aggregate platform-level analytics for admin dashboards."""
    dashboard = get_admin_dashboard()
    publish_admin_dashboard_update(
        {
            "total_users": dashboard["total_users"],
            "total_courses": dashboard["total_courses"],
            "total_revenue": str(dashboard["total_revenue"]),
            "source": "celery",
        }
    )
    return {
        "total_users": dashboard["total_users"],
        "total_courses": dashboard["total_courses"],
        "total_revenue": str(dashboard["total_revenue"]),
    }


@shared_task
def update_course_analytics():
    """Backward-compatible alias for older Celery Beat schedule names."""
    return update_course_analytics_task()
