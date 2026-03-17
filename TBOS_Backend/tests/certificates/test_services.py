from datetime import timedelta

import pytest
from django.utils import timezone

from apps.enrollments.models import Enrollment
from apps.certificates.services.certificate_service import CertificateService
from tests.factories import CourseFactory, EnrollmentFactory, UserFactory


@pytest.mark.django_db
class TestCertificateService:
    def test_generate_certificate_for_completed_enrollment(self, settings):
        settings.FRONTEND_URL = "http://localhost:3000"
        student = UserFactory()
        course = CourseFactory(status="published")
        enrollment = EnrollmentFactory(
            student=student,
            course=course,
            enrollment_status=Enrollment.EnrollmentStatus.COMPLETED,
            completed_at=timezone.now() - timedelta(days=1),
            total_lessons_count=2,
            completed_lessons_count=2,
            is_active=True,
        )

        cert = CertificateService.generate_for_enrollment(enrollment)
        assert cert is not None
        assert cert.student == student
        assert cert.course == course
        assert cert.certificate_url

    def test_verify_certificate_returns_invalid_for_unknown_code(self):
        payload = CertificateService.verify_certificate("does-not-exist")
        assert payload["is_valid"] is False
