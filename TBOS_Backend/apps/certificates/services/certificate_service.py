import os
import secrets
from pathlib import Path

from django.conf import settings
from django.db import IntegrityError, transaction
from django.utils import timezone

from apps.assignments.models import Assignment
from apps.certificates.models import Certificate
from apps.courses.models import Course
from apps.enrollments.models import Enrollment
from apps.quiz.models import Quiz, QuizAttempt


class CertificateService:
    @staticmethod
    def generate_certificate(student, course: Course) -> Certificate:
        existing = Certificate.objects.filter(student=student, course=course).first()
        if existing:
            return existing

        enrollment = Enrollment.objects.filter(
            student=student,
            course=course,
            is_active=True,
        ).first()
        if not enrollment:
            raise ValueError("Enrollment not found for this course.")

        if not CertificateService._is_eligible_for_certificate(enrollment):
            raise ValueError("Student is not eligible for certificate yet.")

        certificate = None
        for _ in range(5):
            try:
                with transaction.atomic():
                    certificate = Certificate.objects.create(
                        student=student,
                        course=course,
                        certificate_number=CertificateService.generate_certificate_number(),
                        verification_code=CertificateService.generate_verification_code(),
                        issue_date=timezone.now().date(),
                    )
                break
            except IntegrityError:
                continue

        if certificate is None:
            raise ValueError("Could not generate certificate. Please retry.")

        certificate.certificate_url = CertificateService.generate_certificate_pdf(certificate)
        certificate.save(update_fields=["certificate_url", "updated_at"])
        return certificate

    @staticmethod
    def generate_certificate_number() -> str:
        year = timezone.now().year
        prefix = f"TBOS-{year}-"
        last_number = (
            Certificate.objects.filter(certificate_number__startswith=prefix)
            .order_by("-certificate_number")
            .values_list("certificate_number", flat=True)
            .first()
        )
        sequence = 1
        if last_number:
            try:
                sequence = int(last_number.split("-")[-1]) + 1
            except (TypeError, ValueError):
                sequence = 1
        return f"{prefix}{sequence:06d}"

    @staticmethod
    def generate_verification_code() -> str:
        for _ in range(10):
            code = secrets.token_urlsafe(24)
            if not Certificate.objects.filter(verification_code=code).exists():
                return code
        raise ValueError("Could not generate a unique verification code.")

    @staticmethod
    def generate_certificate_pdf(certificate: Certificate) -> str:
        try:
            from reportlab.lib.pagesizes import letter
            from reportlab.pdfgen import canvas
        except ImportError as exc:
            raise ValueError("PDF generation library not installed.") from exc

        pdf_path = CertificateService._get_pdf_path(certificate)
        pdf_path.parent.mkdir(parents=True, exist_ok=True)

        verification_url = (
            f"{settings.FRONTEND_URL.rstrip('/')}/certificates/verify/"
            f"{certificate.verification_code}"
        )

        instructor_name = certificate.course.instructor.full_name or certificate.course.instructor.email

        c = canvas.Canvas(str(pdf_path), pagesize=letter)
        c.setTitle(f"Certificate {certificate.certificate_number}")

        c.setFont("Helvetica-Bold", 24)
        c.drawCentredString(306, 730, "Certificate of Completion")

        c.setFont("Helvetica", 14)
        c.drawCentredString(306, 690, "TechBuilt Open School")

        c.setFont("Helvetica", 12)
        c.drawCentredString(306, 640, "This certifies that")

        c.setFont("Helvetica-Bold", 18)
        c.drawCentredString(306, 610, certificate.student.full_name or certificate.student.email)

        c.setFont("Helvetica", 12)
        c.drawCentredString(306, 575, "has successfully completed")

        c.setFont("Helvetica-Bold", 16)
        c.drawCentredString(306, 545, certificate.course.title)

        c.setFont("Helvetica", 11)
        c.drawString(72, 480, f"Instructor: {instructor_name}")
        c.drawString(72, 460, f"Completion Date: {certificate.issue_date.isoformat()}")
        c.drawString(72, 440, f"Certificate Number: {certificate.certificate_number}")
        c.drawString(72, 420, "Verification URL:")
        c.setFont("Helvetica-Oblique", 10)
        c.drawString(72, 402, verification_url)

        c.showPage()
        c.save()

        return (
            f"{settings.FRONTEND_URL.rstrip('/')}/api/v1/certificates/"
            f"{certificate.id}/download/"
        )

    @staticmethod
    def verify_certificate(verification_code: str):
        certificate = (
            Certificate.objects.filter(verification_code=verification_code)
            .select_related("student", "course")
            .first()
        )
        if not certificate:
            return {
                "student_name": "",
                "course_title": "",
                "issue_date": None,
                "is_valid": False,
            }

        return {
            "student_name": certificate.student.full_name or certificate.student.email,
            "course_title": certificate.course.title,
            "issue_date": certificate.issue_date,
            "is_valid": True,
        }

    @staticmethod
    def get_student_certificates(student):
        return Certificate.objects.filter(student=student).select_related("course", "student")

    @staticmethod
    def get_certificate_pdf_path(certificate: Certificate) -> Path:
        return CertificateService._get_pdf_path(certificate)

    @staticmethod
    def generate_for_enrollment(enrollment: Enrollment):
        if not enrollment:
            return None
        return CertificateService.generate_certificate(enrollment.student, enrollment.course)

    @staticmethod
    def _get_pdf_path(certificate: Certificate) -> Path:
        safe_number = certificate.certificate_number.replace(os.sep, "-")
        year = certificate.issue_date.year
        return Path(settings.MEDIA_ROOT) / "certificates" / str(year) / f"{safe_number}.pdf"

    @staticmethod
    def _is_eligible_for_certificate(enrollment: Enrollment) -> bool:
        if enrollment.enrollment_status != Enrollment.EnrollmentStatus.COMPLETED:
            return False
        if enrollment.completed_at is None:
            return False
        if enrollment.total_lessons_count <= 0:
            return False
        if enrollment.completed_lessons_count < enrollment.total_lessons_count:
            return False

        active_quiz_ids = list(
            Quiz.objects.filter(course=enrollment.course, is_active=True).values_list("id", flat=True)
        )
        if active_quiz_ids:
            passed_quizzes = (
                QuizAttempt.objects.filter(
                    quiz_id__in=active_quiz_ids,
                    student=enrollment.student,
                    status=QuizAttempt.Status.SUBMITTED,
                    passed=True,
                )
                .values_list("quiz_id", flat=True)
                .distinct()
                .count()
            )
            if passed_quizzes < len(active_quiz_ids):
                return False

        # Assignment submission can be enforced later as policy evolves.
        Assignment.objects.filter(course=enrollment.course).exists()

        return True


def generate_certificate(student, course: Course) -> Certificate:
    return CertificateService.generate_certificate(student, course)


def generate_certificate_number() -> str:
    return CertificateService.generate_certificate_number()


def generate_verification_code() -> str:
    return CertificateService.generate_verification_code()


def generate_certificate_pdf(certificate: Certificate) -> str:
    return CertificateService.generate_certificate_pdf(certificate)


def verify_certificate(verification_code: str):
    return CertificateService.verify_certificate(verification_code)


def get_student_certificates(student):
    return CertificateService.get_student_certificates(student)
