from rest_framework import serializers

from apps.certificates.models import Certificate


class CertificateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Certificate
        fields = [
            "id",
            "certificate_number",
            "course",
            "student",
            "issue_date",
            "certificate_url",
        ]
        read_only_fields = fields


class CertificateVerificationSerializer(serializers.Serializer):
    student_name = serializers.CharField(read_only=True)
    course_title = serializers.CharField(read_only=True)
    issue_date = serializers.DateField(read_only=True)
    is_valid = serializers.BooleanField(read_only=True)
