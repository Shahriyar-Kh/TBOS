from apps.notifications.services.notification_service import NotificationService


def notify(recipient, notification_type, title, message, reference_id=None):
    return NotificationService.create_notification(
        recipient=recipient,
        title=title,
        message=message,
        notification_type=notification_type,
        reference_id=reference_id,
    )
