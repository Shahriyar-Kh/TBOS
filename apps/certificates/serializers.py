from rest_framework import serializers

from apps.certificates.models import Certificate


class CertificateSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(
        source="student.full_name", read_only=True
    )
    course_title = serializers.CharField(
        source="course.title", read_only=True
    )

    class Meta:
        model = Certificate
        fields = [
            "id",
            "student",
            "student_name",
            "course",
            "course_title",
            "certificate_number",
            "issued_at",
            "pdf_url",
        ]
        read_only_fields = fields


class VerifyCertificateSerializer(serializers.Serializer):
    certificate_number = serializers.CharField()
