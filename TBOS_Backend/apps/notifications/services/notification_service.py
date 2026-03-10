from apps.notifications.models import Notification


class NotificationService:
    @staticmethod
    def send(recipient, notification_type: str, title: str, message: str, action_url: str = ""):
        return Notification.objects.create(
            recipient=recipient,
            notification_type=notification_type,
            title=title,
            message=message,
            action_url=action_url,
        )

    @staticmethod
    def mark_read(notification: Notification):
        notification.is_read = True
        notification.save(update_fields=["is_read", "updated_at"])

    @staticmethod
    def mark_all_read(user):
        Notification.objects.filter(recipient=user, is_read=False).update(is_read=True)

    @staticmethod
    def bulk_notify(recipients, notification_type: str, title: str, message: str, action_url: str = ""):
        notifications = [
            Notification(
                recipient=r,
                notification_type=notification_type,
                title=title,
                message=message,
                action_url=action_url,
            )
            for r in recipients
        ]
        return Notification.objects.bulk_create(notifications, batch_size=1000)
