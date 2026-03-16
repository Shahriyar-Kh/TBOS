import pytest
from django.utils import timezone
from pathlib import Path
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken

from apps.certificates.services.certificate_service import CertificateService
from apps.enrollments.models import Enrollment
from tests.factories import (
    AdminFactory,
    CertificateFactory,
    CourseFactory,
    EnrollmentFactory,
    InstructorFactory,
    UserFactory,
)


BASE = "/api/v1/certificates"
ADMIN_BASE = "/api/v1/admin/certificates/"


def auth(api_client, user):
    token = str(RefreshToken.for_user(user).access_token)
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    return api_client


@pytest.mark.django_db
class TestCertificateStudentAPIs:

    def test_my_certificates_list(self, api_client):
        student = UserFactory()
        cert = CertificateFactory(student=student)
        client = auth(api_client, student)

        resp = client.get(f"{BASE}/my/")

        assert resp.status_code == status.HTTP_200_OK
        assert resp.data["success"] is True
        assert resp.data["data"][0]["certificate_number"] == cert.certificate_number

    def test_download_own_certificate(self, api_client, settings):
        student = UserFactory()
        cert = CertificateFactory(student=student)
        client = auth(api_client, student)

        pdf_path = CertificateService.get_certificate_pdf_path(cert)
        Path(pdf_path).parent.mkdir(parents=True, exist_ok=True)
        Path(pdf_path).write_bytes(b"%PDF-1.4\n%test\n")

        resp = client.get(f"{BASE}/{cert.id}/download/")

        assert resp.status_code == status.HTTP_200_OK
        assert resp["Content-Type"] == "application/pdf"

    def test_download_other_student_certificate_forbidden(self, api_client):
        owner = UserFactory()
        other = UserFactory()
        cert = CertificateFactory(student=owner)
        client = auth(api_client, other)

        resp = client.get(f"{BASE}/{cert.id}/download/")

        assert resp.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
class TestCertificateVerificationAPI:

    def test_verify_certificate_success(self, api_client):
        cert = CertificateFactory()

        resp = api_client.get(f"{BASE}/verify/{cert.verification_code}/")

        assert resp.status_code == status.HTTP_200_OK
        assert resp.data["success"] is True
        assert resp.data["data"]["is_valid"] is True
        assert resp.data["data"]["course_title"] == cert.course.title

    def test_verify_certificate_not_found(self, api_client):
        resp = api_client.get(f"{BASE}/verify/not-found-code/")

        assert resp.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
class TestCertificateAdminAPIs:

    def test_admin_list_certificates(self, api_client):
        admin = AdminFactory()
        CertificateFactory()
        client = auth(api_client, admin)

        resp = client.get(ADMIN_BASE)

        assert resp.status_code == status.HTTP_200_OK
        assert resp.data["success"] is True
        assert len(resp.data["data"]) == 1

    def test_admin_delete_certificate(self, api_client):
        admin = AdminFactory()
        cert = CertificateFactory()
        client = auth(api_client, admin)

        resp = client.delete(f"{ADMIN_BASE}{cert.id}/")

        assert resp.status_code == status.HTTP_200_OK
        assert resp.data["success"] is True


@pytest.mark.django_db
class TestCertificateService:

    def test_generate_certificate_requires_completed_enrollment(self, monkeypatch):
        student = UserFactory()
        instructor = InstructorFactory()
        course = CourseFactory(instructor=instructor)
        EnrollmentFactory(student=student, course=course)

        monkeypatch.setattr(
            CertificateService,
            "generate_certificate_pdf",
            lambda certificate: f"https://tbos.com/api/v1/certificates/{certificate.id}/download/",
        )

        with pytest.raises(ValueError, match="not eligible"):
            CertificateService.generate_certificate(student, course)

    def test_generate_certificate_once_per_course(self, monkeypatch):
        student = UserFactory()
        instructor = InstructorFactory()
        course = CourseFactory(instructor=instructor)
        EnrollmentFactory(
            student=student,
            course=course,
            enrollment_status=Enrollment.EnrollmentStatus.COMPLETED,
            completed_at=timezone.now(),
            total_lessons_count=3,
            completed_lessons_count=3,
        )

        monkeypatch.setattr(
            CertificateService,
            "generate_certificate_pdf",
            lambda certificate: f"https://tbos.com/api/v1/certificates/{certificate.id}/download/",
        )

        first = CertificateService.generate_certificate(student, course)
        second = CertificateService.generate_certificate(student, course)

        assert first.id == second.id
        assert first.certificate_number.startswith("TBOS-")
        assert first.verification_code


@pytest.mark.django_db
def test_completed_enrollment_triggers_certificate_task(
    monkeypatch,
    django_capture_on_commit_callbacks,
):
    student = UserFactory()
    instructor = InstructorFactory()
    course = CourseFactory(instructor=instructor)

    captured = {"enrollment_id": None}

    def fake_delay(enrollment_id):
        captured["enrollment_id"] = enrollment_id

    monkeypatch.setattr(
        "apps.certificates.signals.issue_certificate_for_completed_enrollment.delay",
        fake_delay,
    )

    with django_capture_on_commit_callbacks(execute=True):
        enrollment = EnrollmentFactory(
            student=student,
            course=course,
            enrollment_status=Enrollment.EnrollmentStatus.COMPLETED,
            completed_at=timezone.now(),
            total_lessons_count=2,
            completed_lessons_count=2,
        )

    assert captured["enrollment_id"] == str(enrollment.id)
