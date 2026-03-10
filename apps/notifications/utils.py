from apps.notifications.models import Notification


def notify(recipient, notification_type, title, message, action_url=""):
    """Helper utility to create a notification."""
    return Notification.objects.create(
        recipient=recipient,
        notification_type=notification_type,
        title=title,
        message=message,
        action_url=action_url,
    )
