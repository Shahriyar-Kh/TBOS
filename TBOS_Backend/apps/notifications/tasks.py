from celery import shared_task
from django.contrib.auth import get_user_model

from apps.notifications.models import Notification, NotificationPreference
from apps.notifications.services.notification_service import NotificationService


@shared_task(bind=True, max_retries=3, default_retry_delay=10)
def send_notification_email(self, recipient_id: str, title: str, message: str):
    user_model = get_user_model()
    recipient = user_model.objects.filter(id=recipient_id, is_active=True).first()
    if not recipient:
        return 0
    try:
        return NotificationService.send_email_notification(
            recipient=recipient,
            title=title,
            message=message,
        )
    except Exception as exc:
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=3, default_retry_delay=10)
def send_bulk_notification(self, title: str, message: str):
    user_model = get_user_model()
    recipients = list(user_model.objects.filter(is_active=True).only("id", "email"))
    if not recipients:
        return {"created_count": 0, "recipient_count": 0}

    preferences = {
        pref.user_id: pref
        for pref in NotificationPreference.objects.filter(
            user_id__in=[user.id for user in recipients]
        )
        .only(
            "user_id",
            "email_notifications_enabled",
            "in_app_notifications_enabled",
        )
    }

    notifications = []
    emailed_count = 0
    for recipient in recipients:
        preference = preferences.get(recipient.id)
        if preference is None:
            preference = NotificationPreference.objects.create(user=recipient)
            preferences[recipient.id] = preference

        if preference.in_app_notifications_enabled:
            notifications.append(
                Notification(
                    recipient=recipient,
                    title=title,
                    message=message,
                    notification_type=Notification.NotificationType.SYSTEM_ALERT,
                )
            )

        if preference.email_notifications_enabled and recipient.email:
            try:
                send_notification_email.delay(str(recipient.id), title, message)
            except Exception:
                NotificationService.send_email_notification(
                    recipient=recipient,
                    title=title,
                    message=message,
                )
            emailed_count += 1

    try:
        created = Notification.objects.bulk_create(notifications, batch_size=500)
    except Exception as exc:
        raise self.retry(exc=exc)

    return {
        "created_count": len(created),
        "recipient_count": len(recipients),
        "emailed_count": emailed_count,
    }