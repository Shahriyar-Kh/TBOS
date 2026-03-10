from rest_framework import serializers

from apps.payments.models import BillingDetails, Payment


class PaymentSerializer(serializers.ModelSerializer):
    course_title = serializers.CharField(
        source="course.title", read_only=True, default=""
    )

    class Meta:
        model = Payment
        fields = [
            "id",
            "user",
            "course",
            "course_title",
            "amount",
            "currency",
            "provider",
            "provider_payment_id",
            "status",
            "receipt_url",
            "created_at",
        ]
        read_only_fields = [
            "id",
            "user",
            "provider_payment_id",
            "status",
            "receipt_url",
            "created_at",
        ]


class CheckoutSerializer(serializers.Serializer):
    course_id = serializers.UUIDField()


class BillingDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = BillingDetails
        fields = [
            "id",
            "first_name",
            "last_name",
            "email",
            "address",
            "city",
            "country",
            "postcode",
            "phone",
        ]
        read_only_fields = ["id"]
