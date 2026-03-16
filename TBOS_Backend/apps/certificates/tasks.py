from celery import shared_task

from apps.enrollments.models import Enrollment
from apps.certificates.services.certificate_service import CertificateService


@shared_task(bind=True, max_retries=3, default_retry_delay=10)
def issue_certificate_for_completed_enrollment(self, enrollment_id: str):
    try:
        enrollment = Enrollment.objects.select_related("student", "course").get(id=enrollment_id)
        if enrollment.enrollment_status != Enrollment.EnrollmentStatus.COMPLETED:
            return None
        return str(CertificateService.generate_for_enrollment(enrollment).id)
    except Enrollment.DoesNotExist:
        return None
    except ValueError:
        # Non-eligible enrollment should not be retried.
        return None
    except Exception as exc:
        raise self.retry(exc=exc)
