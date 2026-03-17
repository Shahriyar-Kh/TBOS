import pytest
from django.db import IntegrityError

from tests.factories import CertificateFactory, CourseFactory, UserFactory


@pytest.mark.django_db
class TestCertificateModels:
    def test_certificate_string_contains_number(self):
        certificate = CertificateFactory()
        assert certificate.certificate_number in str(certificate)

    def test_unique_certificate_per_student_course(self):
        student = UserFactory()
        course = CourseFactory()
        CertificateFactory(student=student, course=course)
        with pytest.raises(IntegrityError):
            CertificateFactory(student=student, course=course)
