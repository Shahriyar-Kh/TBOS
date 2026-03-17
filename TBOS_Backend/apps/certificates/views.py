from django.http import FileResponse
from drf_spectacular.utils import extend_schema
from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.views import APIView

from apps.core.api_docs import AUTH_GUIDE, ROLE_ACCESS_GUIDE, CERTIFICATE_EXAMPLE, standard_error_responses, success_example, success_response
from apps.certificates.models import Certificate
from apps.certificates.serializers import (
    CertificateSerializer,
    CertificateVerificationSerializer,
)
from apps.certificates.services.certificate_service import CertificateService
from apps.core.exceptions import api_error, api_success
from apps.core.permissions import IsAdmin, IsStudent


class MyCertificatesView(generics.ListAPIView):
    """GET /api/v1/certificates/my/"""

    serializer_class = CertificateSerializer
    permission_classes = [IsAuthenticated, IsStudent]

    @extend_schema(
        tags=["Certificates"],
        summary="List student certificates",
        description=f"Return certificates issued to the authenticated student.\n\n{AUTH_GUIDE}",
        responses={200: success_response("MyCertificatesResponse", CertificateSerializer, many=True, examples=[success_example("Certificates", "Certificates retrieved.", [CERTIFICATE_EXAMPLE])]), **standard_error_responses(401, 403, 500)},
    )

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Certificate.objects.none()
        return CertificateService.get_student_certificates(self.request.user)

    def list(self, request, *args, **kwargs):
        serializer = self.get_serializer(self.get_queryset(), many=True)
        return api_success(data=serializer.data, message="Certificates retrieved.")


class CertificateDownloadView(APIView):
    """GET /api/v1/certificates/{id}/download/"""

    permission_classes = [IsAuthenticated, IsStudent]

    @extend_schema(
        tags=["Certificates"],
        summary="Download certificate PDF",
        description="Download the generated certificate PDF file for the authenticated student.",
        responses={200: {"description": "PDF file response"}, **standard_error_responses(401, 403, 404, 500)},
    )

    def get(self, request, pk):
        certificate = Certificate.objects.select_related("student", "course").filter(id=pk).first()
        if not certificate:
            return api_error(
                message="Certificate not found.",
                status_code=status.HTTP_404_NOT_FOUND,
            )

        if certificate.student_id != request.user.id:
            return api_error(
                message="You do not have access to this certificate.",
                status_code=status.HTTP_403_FORBIDDEN,
            )

        pdf_path = CertificateService.get_certificate_pdf_path(certificate)
        if not pdf_path.exists():
            CertificateService.generate_certificate_pdf(certificate)

        if not pdf_path.exists():
            return api_error(
                message="Certificate file is not available.",
                status_code=status.HTTP_404_NOT_FOUND,
            )

        return FileResponse(
            open(pdf_path, "rb"),
            as_attachment=True,
            filename=f"{certificate.certificate_number}.pdf",
            content_type="application/pdf",
        )


class VerifyCertificateView(APIView):
    """GET /api/v1/certificates/verify/{verification_code}/"""

    permission_classes = [AllowAny]

    @extend_schema(
        tags=["Certificates"],
        summary="Verify certificate by code",
        auth=[],
        responses={200: success_response("CertificateVerifyResponse", CertificateVerificationSerializer), **standard_error_responses(404, 500)},
    )

    def get(self, request, verification_code):
        result = CertificateService.verify_certificate(verification_code)
        if not result["is_valid"]:
            return api_error(
                message="Certificate not found or invalid.",
                status_code=status.HTTP_404_NOT_FOUND,
            )

        serializer = CertificateVerificationSerializer(result)
        return api_success(
            data=serializer.data,
            message="Certificate verified successfully.",
        )


class AdminCertificateListView(generics.ListAPIView):
    """GET /api/v1/admin/certificates/"""

    serializer_class = CertificateSerializer
    permission_classes = [IsAuthenticated, IsAdmin]
    queryset = Certificate.objects.select_related("student", "course").all()

    @extend_schema(
        tags=["Certificates"],
        summary="List all certificates",
        description=f"Administrative certificate ledger.\n\n{AUTH_GUIDE}\n\n{ROLE_ACCESS_GUIDE}",
        responses={200: success_response("AdminCertificatesResponse", CertificateSerializer, many=True), **standard_error_responses(401, 403, 500)},
    )

    def list(self, request, *args, **kwargs):
        serializer = self.get_serializer(self.get_queryset(), many=True)
        return api_success(data=serializer.data, message="Certificates retrieved.")


class AdminCertificateDeleteView(APIView):
    """DELETE /api/v1/admin/certificates/{id}/"""

    permission_classes = [IsAuthenticated, IsAdmin]

    @extend_schema(
        tags=["Certificates"],
        summary="Delete certificate",
        responses={200: success_response("AdminCertificateDeleteResponse", None), **standard_error_responses(401, 403, 404, 500)},
    )

    def delete(self, request, pk):
        certificate = Certificate.objects.filter(id=pk).first()
        if not certificate:
            return api_error(
                message="Certificate not found.",
                status_code=status.HTTP_404_NOT_FOUND,
            )
        certificate.delete()
        return api_success(data={}, message="Certificate deleted successfully.")
