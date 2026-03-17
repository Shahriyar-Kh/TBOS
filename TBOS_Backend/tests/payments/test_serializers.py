import pytest

from apps.payments.serializers import CheckoutSerializer, PaymentVerificationSerializer


@pytest.mark.django_db
class TestPaymentSerializers:
    def test_checkout_serializer_validates_nested_billing_details(self):
        serializer = CheckoutSerializer(
            data={
                "course_id": "11111111-1111-1111-1111-111111111111",
                "billing_details": {
                    "first_name": "Ada",
                    "last_name": "Lovelace",
                    "email": "ada@example.com",
                    "country": "Bangladesh",
                    "city": "Dhaka",
                    "postal_code": "1207",
                    "address": "Road 1",
                    "phone_number": "+8801700000000",
                },
            }
        )
        assert serializer.is_valid(), serializer.errors

    def test_payment_verification_serializer_requires_transaction_id(self):
        serializer = PaymentVerificationSerializer(
            data={"order_id": "11111111-1111-1111-1111-111111111111"}
        )
        assert not serializer.is_valid()
        assert "transaction_id" in serializer.errors
