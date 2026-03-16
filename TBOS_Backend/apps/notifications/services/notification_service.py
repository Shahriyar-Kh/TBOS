import logging

from django.conf import settings
from django.core.mail import send_mail
from django.db import transaction

from apps.enrollments.models import Enrollment
from apps.notifications.models import Notification, NotificationPreference

logger = logging.getLogger(__name__)


class NotificationService:
    @staticmethod
    def create_notification(
        *,
        recipient,
        title: str,
        message: str,
        notification_type: str,
        reference_id=None,
    ):
        preference = NotificationService.get_or_create_preferences(recipient)
        should_create_in_app = NotificationService._channel_enabled(
            preference=preference,
            notification_type=notification_type,
            channel="in_app",
        )
        should_send_email = NotificationService._channel_enabled(
            preference=preference,
            notification_type=notification_type,
            channel="email",
        )

        notification = None
        if should_create_in_app:
            notification = Notification.objects.create(
                recipient=recipient,
                title=title,
                message=message,
                notification_type=notification_type,
                reference_id=reference_id,
            )

        if should_send_email and recipient.email:
            def dispatch_email():
                from apps.notifications.tasks import send_notification_email

                try:
                    send_notification_email.delay(str(recipient.id), title, message)
                except Exception:
                    logger.warning(
                        "Celery unavailable for notification email; falling back to sync send.",
                        exc_info=True,
                    )
                    NotificationService.send_email_notification(
                        recipient=recipient,
                        title=title,
                        message=message,
                    )

            transaction.on_commit(dispatch_email)

        return notification

    @staticmethod
    def send_email_notification(*, recipient, title: str, message: str) -> int:
        if not recipient.email:
            return 0

        from_email = getattr(settings, "DEFAULT_FROM_EMAIL", "no-reply@tbos.local")
        return send_mail(
            subject=title,
            message=message,
            from_email=from_email,
            recipient_list=[recipient.email],
            fail_silently=False,
        )

    @staticmethod
    def notify_course_students(
        *,
        course,
        title: str,
        message: str,
        notification_type: str = Notification.NotificationType.COURSE_UPDATE,
        reference_id=None,
    ):
        enrollments = (
            Enrollment.objects.filter(course=course, is_active=True)
            .select_related("student")
            .distinct()
        )
        notifications = []
        for enrollment in enrollments:
            notification = NotificationService.create_notification(
                recipient=enrollment.student,
                title=title,
                message=message,
                notification_type=notification_type,
                reference_id=reference_id,
            )
            if notification is not None:
                notifications.append(notification)
        return notifications

    @staticmethod
    def notify_assignment_deadline(*, assignment):
        due_date_display = assignment.due_date.isoformat() if assignment.due_date else "soon"
        return NotificationService.notify_course_students(
            course=assignment.course,
            title=f"Assignment deadline: {assignment.title}",
            message=(
                f"The assignment '{assignment.title}' is available. "
                f"Submit before {due_date_display}."
            ),
            notification_type=Notification.NotificationType.ASSIGNMENT_DEADLINE,
            reference_id=assignment.id,
        )

    @staticmethod
    def notify_certificate_issued(*, certificate):
        return NotificationService.create_notification(
            recipient=certificate.student,
            title="Certificate issued",
            message=(
                f"Your certificate for '{certificate.course.title}' is now available."
            ),
            notification_type=Notification.NotificationType.CERTIFICATE_ISSUED,
            reference_id=certificate.id,
        )

    @staticmethod
    def mark_notification_read(*, notification_id, user):
        notification = Notification.objects.filter(
            id=notification_id,
            recipient=user,
        ).first()
        if not notification:
            return None
        if not notification.is_read:
            notification.is_read = True
            notification.save(update_fields=["is_read", "updated_at"])
        return notification

    @staticmethod
    def mark_all_notifications_read(*, user) -> int:
        return Notification.objects.filter(recipient=user, is_read=False).update(is_read=True)

    @staticmethod
    def get_user_notifications(*, user, is_read=None):
        queryset = Notification.objects.filter(recipient=user).select_related("recipient")
        if is_read is not None:
            queryset = queryset.filter(is_read=is_read)
        return queryset.order_by("is_read", "-created_at")

    @staticmethod
    def get_or_create_preferences(user):
        preference, _ = NotificationPreference.objects.get_or_create(user=user)
        return preference

    @staticmethod
    def _channel_enabled(*, preference: NotificationPreference, notification_type: str, channel: str) -> bool:
        global_enabled = (
            preference.in_app_notifications_enabled
            if channel == "in_app"
            else preference.email_notifications_enabled
        )
        if not global_enabled:
            return False

        if notification_type in {
            Notification.NotificationType.COURSE_UPDATE,
            Notification.NotificationType.NEW_LESSON,
        }:
            return preference.course_updates
        if notification_type == Notification.NotificationType.ASSIGNMENT_DEADLINE:
            return preference.assignment_notifications
        if notification_type == Notification.NotificationType.QUIZ_AVAILABLE:
            return preference.quiz_notifications
        return True
