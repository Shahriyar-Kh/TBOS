import uuid

from apps.certificates.models import Certificate
from apps.courses.models import Course
from apps.enrollments.models import Enrollment


class CertificateService:
    @staticmethod
    def issue_certificate(student, course: Course) -> Certificate:
        enrollment = Enrollment.objects.filter(
            student=student, course=course, completed_at__isnull=False
        ).first()
        if not enrollment:
            raise ValueError("Course not completed yet.")

        certificate, created = Certificate.objects.get_or_create(
            student=student,
            course=course,
            defaults={"certificate_number": CertificateService._generate_number()},
        )
        if not created:
            raise ValueError("Certificate already issued.")
        return certificate

    @staticmethod
    def verify_certificate(certificate_number: str):
        return Certificate.objects.filter(
            certificate_number=certificate_number
        ).select_related("student", "course").first()

    @staticmethod
    def _generate_number() -> str:
        return f"TBOS-{uuid.uuid4().hex[:12].upper()}"
