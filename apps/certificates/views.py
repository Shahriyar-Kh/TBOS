from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.permissions import IsStudent, IsAdmin
from apps.certificates.models import Certificate
from apps.certificates.serializers import (
    CertificateSerializer,
    VerifyCertificateSerializer,
)
from apps.enrollments.models import Enrollment


class MyCertificatesView(generics.ListAPIView):
    """
    GET /api/v1/certificates/my/
    List certificates for the authenticated student.
    """
    serializer_class = CertificateSerializer
    permission_classes = [IsAuthenticated, IsStudent]

    def get_queryset(self):
        return Certificate.objects.filter(
            student=self.request.user
        ).select_related("course")


class RequestCertificateView(APIView):
    """
    POST /api/v1/certificates/request/
    Request a certificate for a completed course.
    """
    permission_classes = [IsAuthenticated, IsStudent]

    def post(self, request):
        course_id = request.data.get("course_id")
        if not course_id:
            return Response(
                {"detail": "course_id is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        enrollment = Enrollment.objects.filter(
            student=request.user,
            course_id=course_id,
            completed_at__isnull=False,
        ).first()

        if not enrollment:
            return Response(
                {"detail": "Course not completed yet."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        cert, created = Certificate.objects.get_or_create(
            student=request.user,
            course_id=course_id,
        )

        if not created:
            return Response(
                {"detail": "Certificate already issued."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            CertificateSerializer(cert).data,
            status=status.HTTP_201_CREATED,
        )


class VerifyCertificateView(APIView):
    """
    POST /api/v1/certificates/verify/
    Public endpoint to verify a certificate by its number.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = VerifyCertificateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            cert = Certificate.objects.select_related(
                "student", "course"
            ).get(
                certificate_number=serializer.validated_data["certificate_number"]
            )
        except Certificate.DoesNotExist:
            return Response(
                {"valid": False, "detail": "Certificate not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        return Response(
            {
                "valid": True,
                "certificate": CertificateSerializer(cert).data,
            }
        )


class AdminCertificateListView(generics.ListAPIView):
    """
    GET /api/v1/certificates/admin/
    Admin view of all certificates.
    """
    serializer_class = CertificateSerializer
    permission_classes = [IsAuthenticated, IsAdmin]
    queryset = Certificate.objects.select_related("student", "course").all()
