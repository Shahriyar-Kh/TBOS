from rest_framework import serializers

from apps.courses.serializers import CourseListSerializer
from apps.payments.models import BillingDetails, Order, Payment


class BillingDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = BillingDetails
        fields = [
            "id",
            "first_name",
            "last_name",
            "email",
            "country",
            "city",
            "postal_code",
            "address",
            "phone_number",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class CheckoutSerializer(serializers.Serializer):
    course_id = serializers.UUIDField()
    billing_details = BillingDetailsSerializer()


class PaymentVerificationSerializer(serializers.Serializer):
    order_id = serializers.UUIDField()
    transaction_id = serializers.CharField(max_length=255)


class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = [
            "id",
            "order",
            "payment_provider",
            "transaction_id",
            "payment_status",
            "payment_data",
            "created_at",
        ]
        read_only_fields = fields


class OrderSerializer(serializers.ModelSerializer):
    course = CourseListSerializer(read_only=True)
    status = serializers.CharField(source="order_status", read_only=True)
    payment_method = serializers.CharField(read_only=True)

    class Meta:
        model = Order
        fields = [
            "id",
            "order_number",
            "course",
            "amount",
            "currency",
            "status",
            "payment_method",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields


class OrderDetailSerializer(OrderSerializer):
    payments = PaymentSerializer(many=True, read_only=True)

    class Meta(OrderSerializer.Meta):
        fields = OrderSerializer.Meta.fields + ["payments"]


class RefundOrderSerializer(serializers.Serializer):
    order_id = serializers.UUIDField()
