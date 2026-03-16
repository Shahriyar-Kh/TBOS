from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db import transaction

from apps.certificates.tasks import issue_certificate_for_completed_enrollment
from apps.enrollments.models import Enrollment


@receiver(post_save, sender=Enrollment)
def auto_issue_certificate_on_completion(sender, instance, **kwargs):
    if instance.enrollment_status != Enrollment.EnrollmentStatus.COMPLETED:
        return
    if instance.completed_at is None:
        return
    if instance.student.certificates.filter(course=instance.course).exists():
        return

    transaction.on_commit(
        lambda: issue_certificate_for_completed_enrollment.delay(str(instance.id))
    )
