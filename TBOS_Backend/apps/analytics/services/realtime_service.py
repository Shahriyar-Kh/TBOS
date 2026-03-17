from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer


def student_group(user_id):
    return f"analytics_student_{user_id}"


def instructor_group(user_id):
    return f"analytics_instructor_{user_id}"


def admin_group():
    return "analytics_admin"


def course_group(course_id):
    return f"analytics_course_{course_id}"


def _publish(group_name, event, data):
    channel_layer = get_channel_layer()
    if channel_layer is None:
        return

    async_to_sync(channel_layer.group_send)(
        group_name,
        {
            "type": "dashboard.update",
            "event": event,
            "data": data,
        },
    )


def publish_student_dashboard_update(user_id, payload):
    _publish(student_group(user_id), "student_dashboard_updated", payload)


def publish_instructor_dashboard_update(user_id, payload):
    _publish(instructor_group(user_id), "instructor_dashboard_updated", payload)


def publish_admin_dashboard_update(payload):
    _publish(admin_group(), "admin_dashboard_updated", payload)


def publish_course_analytics_update(course_id, payload):
    _publish(course_group(course_id), "course_analytics_updated", payload)
