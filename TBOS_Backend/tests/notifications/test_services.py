from unittest.mock import patch

import pytest

from apps.notifications.models import Notification
from apps.notifications.services.notification_service import NotificationService
from tests.factories import (
    AssignmentFactory,
    CertificateFactory,
    CourseFactory,
    EnrollmentFactory,
    NotificationFactory,
    NotificationPreferenceFactory,
    UserFactory,
)


@pytest.mark.django_db
class TestNotificationServiceCreateNotification:
    @patch(
        "apps.notifications.services.notification_service.transaction.on_commit",
        side_effect=lambda callback: callback(),
    )
    @patch("apps.notifications.tasks.send_notification_email.delay")
    def test_create_notification_creates_in_app_and_queues_email(self, mocked_delay, mocked_on_commit):
        user = UserFactory(email="notify@example.com")
        NotificationPreferenceFactory(user=user)

        notification = NotificationService.create_notification(
            recipient=user,
            title="New lesson",
            message="A lesson has been published.",
            notification_type=Notification.NotificationType.NEW_LESSON,
        )

        assert notification is not None
        assert notification.recipient == user
        assert notification.notification_type == Notification.NotificationType.NEW_LESSON
        mocked_delay.assert_called_once_with(str(user.id), "New lesson", "A lesson has been published.")
        mocked_on_commit.assert_called_once()

    @patch(
        "apps.notifications.services.notification_service.transaction.on_commit",
        side_effect=lambda callback: callback(),
    )
    @patch("apps.notifications.tasks.send_notification_email.delay")
    def test_create_notification_respects_disabled_in_app_preference(self, mocked_delay, mocked_on_commit):
        user = UserFactory(email="email-only@example.com")
        NotificationPreferenceFactory(user=user, in_app_notifications_enabled=False)

        notification = NotificationService.create_notification(
            recipient=user,
            title="Course update",
            message="Course details changed.",
            notification_type=Notification.NotificationType.COURSE_UPDATE,
        )

        assert notification is None
        assert Notification.objects.filter(recipient=user).count() == 0
        mocked_delay.assert_called_once()
        mocked_on_commit.assert_called_once()

    @patch("apps.notifications.tasks.send_notification_email.delay", side_effect=RuntimeError("broker down"))
    @patch("apps.notifications.services.notification_service.NotificationService.send_email_notification")
    @patch(
        "apps.notifications.services.notification_service.transaction.on_commit",
        side_effect=lambda callback: callback(),
    )
    def test_create_notification_falls_back_to_sync_email(self, mocked_on_commit, mocked_send_email, mocked_delay):
        user = UserFactory(email="fallback@example.com")
        NotificationPreferenceFactory(user=user)

        NotificationService.create_notification(
            recipient=user,
            title="System alert",
            message="Important update.",
            notification_type=Notification.NotificationType.SYSTEM_ALERT,
        )

        mocked_delay.assert_called_once()
        mocked_send_email.assert_called_once_with(
            recipient=user,
            title="System alert",
            message="Important update.",
        )
        mocked_on_commit.assert_called_once()

    @patch("apps.notifications.tasks.send_notification_email.delay")
    @patch(
        "apps.notifications.services.notification_service.transaction.on_commit",
        side_effect=lambda callback: callback(),
    )
    def test_create_notification_skips_email_when_email_preferences_disabled(self, mocked_on_commit, mocked_delay):
        user = UserFactory(email="no-email@example.com")
        NotificationPreferenceFactory(user=user, email_notifications_enabled=False)

        notification = NotificationService.create_notification(
            recipient=user,
            title="Certificate",
            message="Issued successfully.",
            notification_type=Notification.NotificationType.CERTIFICATE_ISSUED,
        )

        assert notification is not None
        mocked_delay.assert_not_called()
        mocked_on_commit.assert_not_called()


@pytest.mark.django_db
class TestNotificationServiceQueries:
    def test_mark_notification_read(self):
        user = UserFactory()
        notification = NotificationFactory(recipient=user, is_read=False)

        result = NotificationService.mark_notification_read(
            notification_id=notification.id,
            user=user,
        )
        notification.refresh_from_db()

        assert result.id == notification.id
        assert notification.is_read is True

    def test_mark_notification_read_returns_none_for_other_user(self):
        notification = NotificationFactory()
        another_user = UserFactory()

        result = NotificationService.mark_notification_read(
            notification_id=notification.id,
            user=another_user,
        )

        assert result is None

    def test_mark_all_notifications_read(self):
        user = UserFactory()
        NotificationFactory.create_batch(2, recipient=user, is_read=False)
        NotificationFactory(recipient=user, is_read=True)

        updated_count = NotificationService.mark_all_notifications_read(user=user)

        assert updated_count == 2
        assert Notification.objects.filter(recipient=user, is_read=False).count() == 0

    def test_get_user_notifications_filters_and_orders(self):
        user = UserFactory()
        read_notification = NotificationFactory(recipient=user, is_read=True)
        unread_notification = NotificationFactory(recipient=user, is_read=False)
        NotificationFactory()

        notifications = list(NotificationService.get_user_notifications(user=user))
        unread_only = list(NotificationService.get_user_notifications(user=user, is_read=False))

        assert notifications[0] == unread_notification
        assert read_notification in notifications
        assert unread_only == [unread_notification]

    def test_get_or_create_preferences_returns_existing_row(self):
        user = UserFactory()
        existing = NotificationPreferenceFactory(user=user, quiz_notifications=False)

        preference = NotificationService.get_or_create_preferences(user)

        assert preference.id == existing.id
        assert preference.quiz_notifications is False


@pytest.mark.django_db
class TestNotificationServiceEventHelpers:
    @patch("apps.notifications.services.notification_service.NotificationService.create_notification")
    def test_notify_course_students_notifies_active_enrollments(self, mocked_create_notification):
        course = CourseFactory()
        active_one = UserFactory()
        active_two = UserFactory()
        inactive_user = UserFactory()
        EnrollmentFactory(course=course, student=active_one, is_active=True)
        EnrollmentFactory(course=course, student=active_two, is_active=True)
        EnrollmentFactory(course=course, student=inactive_user, is_active=False)

        NotificationService.notify_course_students(
            course=course,
            title="Course updated",
            message="New resources added.",
            notification_type=Notification.NotificationType.COURSE_UPDATE,
        )

        recipients = [call.kwargs["recipient"] for call in mocked_create_notification.call_args_list]
        assert active_one in recipients
        assert active_two in recipients
        assert inactive_user not in recipients
        assert mocked_create_notification.call_count == 2

    @patch("apps.notifications.services.notification_service.NotificationService.notify_course_students")
    def test_notify_assignment_deadline_builds_expected_payload(self, mocked_notify_course_students):
        assignment = AssignmentFactory()
        mocked_notify_course_students.reset_mock()

        NotificationService.notify_assignment_deadline(assignment=assignment)

        mocked_notify_course_students.assert_called_once()
        kwargs = mocked_notify_course_students.call_args.kwargs
        assert kwargs["course"] == assignment.course
        assert kwargs["notification_type"] == Notification.NotificationType.ASSIGNMENT_DEADLINE
        assert kwargs["reference_id"] == assignment.id
        assert assignment.title in kwargs["title"]

    @patch("apps.notifications.services.notification_service.NotificationService.create_notification")
    def test_notify_certificate_issued_targets_certificate_student(self, mocked_create_notification):
        certificate = CertificateFactory()
        mocked_create_notification.reset_mock()

        NotificationService.notify_certificate_issued(certificate=certificate)

        mocked_create_notification.assert_called_once()
        kwargs = mocked_create_notification.call_args.kwargs
        assert kwargs["recipient"] == certificate.student
        assert kwargs["notification_type"] == Notification.NotificationType.CERTIFICATE_ISSUED
        assert kwargs["reference_id"] == certificate.id


@pytest.mark.django_db
class TestNotificationServiceEmail:
    @patch("apps.notifications.services.notification_service.send_mail")
    def test_send_email_notification_uses_default_from_email(self, mocked_send_mail, settings):
        settings.DEFAULT_FROM_EMAIL = "noreply@tbos.test"
        user = UserFactory(email="mail@example.com")

        NotificationService.send_email_notification(
            recipient=user,
            title="Welcome",
            message="Hello there",
        )

        mocked_send_mail.assert_called_once_with(
            subject="Welcome",
            message="Hello there",
            from_email="noreply@tbos.test",
            recipient_list=["mail@example.com"],
            fail_silently=False,
        )

    def test_channel_enabled_uses_category_preferences(self):
        preference = NotificationPreferenceFactory(
            course_updates=False,
            assignment_notifications=False,
            quiz_notifications=True,
        )

        assert NotificationService._channel_enabled(
            preference=preference,
            notification_type=Notification.NotificationType.COURSE_UPDATE,
            channel="in_app",
        ) is False
        assert NotificationService._channel_enabled(
            preference=preference,
            notification_type=Notification.NotificationType.ASSIGNMENT_DEADLINE,
            channel="email",
        ) is False
        assert NotificationService._channel_enabled(
            preference=preference,
            notification_type=Notification.NotificationType.QUIZ_AVAILABLE,
            channel="in_app",
        ) is True