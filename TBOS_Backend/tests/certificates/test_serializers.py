import pytest

from apps.certificates.serializers import CertificateVerificationSerializer
from tests.factories import CertificateFactory


@pytest.mark.django_db
class TestCertificateSerializers:
    def test_certificate_verification_serializer_output_shape(self):
        cert = CertificateFactory()
        serializer = CertificateVerificationSerializer(
            {
                "student_name": cert.student.full_name or cert.student.email,
                "course_title": cert.course.title,
                "issue_date": cert.issue_date,
                "is_valid": True,
            }
        )
        data = serializer.data
        assert data["is_valid"] is True
        assert "course_title" in data
