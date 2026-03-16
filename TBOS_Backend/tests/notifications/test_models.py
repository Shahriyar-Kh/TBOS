import pytest
from datetime import timedelta
from django.utils import timezone

from apps.notifications.models import Notification, NotificationPreference
from tests.factories import NotificationFactory, NotificationPreferenceFactory, UserFactory


@pytest.mark.django_db
class TestNotificationModel:
    def test_create_notification(self):
        notification = NotificationFactory()

        assert notification.pk is not None
        assert notification.notification_type == Notification.NotificationType.SYSTEM_ALERT
        assert notification.is_read is False
        assert notification.created_at is not None

    def test_notification_str(self):
        notification = NotificationFactory(title="Course updated")

        assert "Course updated" in str(notification)
        assert notification.recipient.email in str(notification)

    def test_notification_ordering_unread_first_then_latest(self):
        user = UserFactory()
        older_unread = NotificationFactory(recipient=user, is_read=False)
        newer_unread = NotificationFactory(recipient=user, is_read=False)
        read_notification = NotificationFactory(recipient=user, is_read=True)

        Notification.objects.filter(id=older_unread.id).update(
            created_at=timezone.now() - timedelta(minutes=5)
        )
        Notification.objects.filter(id=newer_unread.id).update(
            created_at=timezone.now() - timedelta(minutes=1)
        )
        older_unread.refresh_from_db()
        newer_unread.refresh_from_db()

        notifications = list(Notification.objects.filter(recipient=user))

        assert notifications[0] == newer_unread
        assert notifications[1] == older_unread
        assert notifications[-1] == read_notification

    def test_notification_type_choices(self):
        for notification_type in [choice[0] for choice in Notification.NotificationType.choices]:
            notification = NotificationFactory(notification_type=notification_type)
            assert notification.notification_type == notification_type


@pytest.mark.django_db
class TestNotificationPreferenceModel:
    def test_create_notification_preference(self):
        preference = NotificationPreferenceFactory()

        assert preference.pk is not None
        assert preference.email_notifications_enabled is True
        assert preference.in_app_notifications_enabled is True
        assert preference.course_updates is True
        assert preference.assignment_notifications is True
        assert preference.quiz_notifications is True

    def test_notification_preference_str(self):
        preference = NotificationPreferenceFactory()

        assert preference.user.email in str(preference)

    def test_notification_preference_is_one_to_one_with_user(self):
        user = UserFactory()
        existing = NotificationPreferenceFactory(user=user)
        duplicate = NotificationPreferenceFactory(user=user, quiz_notifications=False)

        assert existing.id == duplicate.id
        assert NotificationPreference.objects.filter(user=user).count() == 1
        assert duplicate.quiz_notifications is False