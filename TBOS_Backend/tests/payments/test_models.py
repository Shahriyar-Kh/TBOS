"""Tests for Payment module models: Order, Payment, BillingDetails."""
import pytest

from apps.payments.models import BillingDetails, Order, Payment
from tests.factories import (
    BillingDetailsFactory,
    CourseFactory,
    OrderFactory,
    PaymentFactory,
    UserFactory,
)


# ──────────────────────────────────────────────
# Order
# ──────────────────────────────────────────────


@pytest.mark.django_db
class TestOrderModel:
    def test_create_order(self):
        order = OrderFactory()
        assert order.pk is not None
        assert order.order_status == Order.OrderStatus.PENDING
        assert order.payment_method == Order.PaymentMethod.STRIPE
        assert order.currency == "USD"

    def test_str_representation(self):
        order = OrderFactory()
        s = str(order)
        assert order.order_number in s
        assert order.student.email in s
        assert order.course.title in s

    def test_order_status_choices(self):
        choices = [c[0] for c in Order.OrderStatus.choices]
        assert "PENDING" in choices
        assert "COMPLETED" in choices
        assert "FAILED" in choices
        assert "REFUNDED" in choices

    def test_payment_method_choices(self):
        choices = [c[0] for c in Order.PaymentMethod.choices]
        assert "STRIPE" in choices
        assert "EASYPAISA" in choices

    def test_unique_student_course_constraint(self):
        order = OrderFactory()
        with pytest.raises(Exception):
            Order.objects.create(
                student=order.student,
                course=order.course,
                order_number=f"{order.order_number}-DUP",
                amount=order.amount,
                currency=order.currency,
                order_status=Order.OrderStatus.PENDING,
                payment_method=Order.PaymentMethod.STRIPE,
            )

    def test_order_number_unique(self):
        order = OrderFactory()
        with pytest.raises(Exception):
            OrderFactory(
                order_number=order.order_number,
                student=UserFactory(),
                course=CourseFactory(is_free=False, price=50, discount_price=40, status="published"),
            )

    def test_defaults(self):
        order = OrderFactory()
        assert order.currency == "USD"
        assert order.payment_method == Order.PaymentMethod.STRIPE
        assert order.order_status == Order.OrderStatus.PENDING

    def test_amount_reflects_course_price(self):
        course = CourseFactory(is_free=False, price=99, discount_price=0, status="published")
        order = OrderFactory(course=course, amount=course.effective_price)
        assert order.amount == course.effective_price

    def test_can_transition_status_to_completed(self):
        order = OrderFactory()
        order.order_status = Order.OrderStatus.COMPLETED
        order.save(update_fields=["order_status", "updated_at"])
        order.refresh_from_db()
        assert order.order_status == Order.OrderStatus.COMPLETED

    def test_can_transition_status_to_refunded(self):
        order = OrderFactory(order_status=Order.OrderStatus.COMPLETED)
        order.order_status = Order.OrderStatus.REFUNDED
        order.save(update_fields=["order_status", "updated_at"])
        order.refresh_from_db()
        assert order.order_status == Order.OrderStatus.REFUNDED


# ──────────────────────────────────────────────
# Payment
# ──────────────────────────────────────────────


@pytest.mark.django_db
class TestPaymentModel:
    def test_create_payment(self):
        payment = PaymentFactory()
        assert payment.pk is not None
        assert payment.payment_status == Payment.PaymentStatus.PENDING
        assert payment.payment_provider == Payment.Provider.STRIPE
        assert payment.transaction_id == ""
        assert payment.payment_data == {}

    def test_str_representation(self):
        payment = PaymentFactory()
        s = str(payment)
        assert payment.order.order_number in s
        assert payment.payment_provider in s
        assert payment.payment_status in s

    def test_payment_status_choices(self):
        choices = [c[0] for c in Payment.PaymentStatus.choices]
        assert "PENDING" in choices
        assert "SUCCESS" in choices
        assert "FAILED" in choices
        assert "REFUNDED" in choices

    def test_provider_choices(self):
        choices = [c[0] for c in Payment.Provider.choices]
        assert "STRIPE" in choices
        assert "EASYPAISA" in choices

    def test_cascade_delete_with_order(self):
        payment = PaymentFactory()
        order_id = payment.order_id
        payment.order.delete()
        assert not Payment.objects.filter(order_id=order_id).exists()

    def test_payment_data_json_field_stores_and_retrieves(self):
        payment = PaymentFactory()
        payload = {"checkout_session_id": "cs_test_123", "checkout_url": "https://stripe.com"}
        payment.payment_data = payload
        payment.save(update_fields=["payment_data", "updated_at"])
        payment.refresh_from_db()
        assert payment.payment_data["checkout_session_id"] == "cs_test_123"

    def test_payment_data_stores_refund_info(self):
        payment = PaymentFactory(
            payment_status=Payment.PaymentStatus.SUCCESS,
            transaction_id="pi_refund_test",
        )
        payment.payment_data = {**payment.payment_data, "refund": {"id": "re_1", "status": "succeeded"}}
        payment.payment_status = Payment.PaymentStatus.REFUNDED
        payment.save(update_fields=["payment_data", "payment_status", "updated_at"])
        payment.refresh_from_db()
        assert payment.payment_status == Payment.PaymentStatus.REFUNDED
        assert "refund" in payment.payment_data

    def test_multiple_payments_linked_to_same_order(self):
        order = OrderFactory()
        PaymentFactory(order=order)
        PaymentFactory(order=order, payment_status=Payment.PaymentStatus.SUCCESS)
        assert Payment.objects.filter(order=order).count() == 2


# ──────────────────────────────────────────────
# BillingDetails
# ──────────────────────────────────────────────


@pytest.mark.django_db
class TestBillingDetailsModel:
    def test_create_billing_details(self):
        billing = BillingDetailsFactory()
        assert billing.pk is not None
        assert billing.country == "Bangladesh"
        assert billing.city == "Dhaka"
        assert billing.postal_code == "1207"

    def test_str_representation(self):
        billing = BillingDetailsFactory()
        s = str(billing)
        assert billing.first_name in s
        assert billing.last_name in s

    def test_user_cascade_delete(self):
        billing = BillingDetailsFactory()
        user_id = billing.user_id
        billing.user.delete()
        assert not BillingDetails.objects.filter(user_id=user_id).exists()

    def test_multiple_billing_details_per_user(self):
        user = UserFactory()
        BillingDetailsFactory(user=user)
        BillingDetailsFactory(user=user)
        assert BillingDetails.objects.filter(user=user).count() == 2

    def test_optional_phone_number(self):
        billing = BillingDetailsFactory(phone_number="")
        billing.refresh_from_db()
        assert billing.phone_number == ""
