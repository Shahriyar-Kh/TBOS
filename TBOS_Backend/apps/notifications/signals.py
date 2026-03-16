from django.contrib.auth import get_user_model
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from apps.assignments.models import Assignment
from apps.certificates.models import Certificate
from apps.lessons.models import Lesson
from apps.notifications.models import Notification, NotificationPreference
from apps.notifications.services.notification_service import NotificationService
from apps.quiz.models import Quiz

User = get_user_model()


@receiver(post_save, sender=User)
def create_notification_preferences(sender, instance, created, **kwargs):
    if created:
        NotificationPreference.objects.get_or_create(user=instance)


@receiver(post_save, sender=Lesson)
def notify_new_lesson(sender, instance, created, **kwargs):
    if not created:
        return

    NotificationService.notify_course_students(
        course=instance.section.course,
        title=f"New lesson available: {instance.title}",
        message=f"A new lesson has been added to {instance.section.course.title}.",
        notification_type=Notification.NotificationType.NEW_LESSON,
        reference_id=instance.id,
    )


@receiver(pre_save, sender=Quiz)
def capture_quiz_state(sender, instance, **kwargs):
    if not instance.pk:
        instance._previous_is_active = False
        return
    previous = sender.objects.filter(pk=instance.pk).only("is_active").first()
    instance._previous_is_active = previous.is_active if previous else False


@receiver(post_save, sender=Quiz)
def notify_quiz_available(sender, instance, created, **kwargs):
    became_available = instance.is_active and (created or not getattr(instance, "_previous_is_active", False))
    if not became_available:
        return

    NotificationService.notify_course_students(
        course=instance.course,
        title=f"Quiz available: {instance.title}",
        message=f"A new quiz is now available in {instance.course.title}.",
        notification_type=Notification.NotificationType.QUIZ_AVAILABLE,
        reference_id=instance.id,
    )


@receiver(pre_save, sender=Assignment)
def capture_assignment_state(sender, instance, **kwargs):
    if not instance.pk:
        instance._previous_is_published = False
        instance._previous_due_date = None
        return
    previous = sender.objects.filter(pk=instance.pk).only("is_published", "due_date").first()
    instance._previous_is_published = previous.is_published if previous else False
    instance._previous_due_date = previous.due_date if previous else None


@receiver(post_save, sender=Assignment)
def notify_assignment_publish_or_deadline(sender, instance, created, **kwargs):
    should_notify = False
    if instance.is_published and created:
        should_notify = True
    elif instance.is_published and not getattr(instance, "_previous_is_published", False):
        should_notify = True
    elif instance.is_published and instance.due_date and instance.due_date != getattr(instance, "_previous_due_date", None):
        should_notify = True

    if not should_notify:
        return

    NotificationService.notify_assignment_deadline(assignment=instance)


@receiver(post_save, sender=Certificate)
def notify_certificate_created(sender, instance, created, **kwargs):
    if created:
        NotificationService.notify_certificate_issued(certificate=instance)