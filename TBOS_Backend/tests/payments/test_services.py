"""Tests for Payment service layer: create_order, checkout session, success/failure/refund."""
import pytest
from decimal import Decimal
from types import SimpleNamespace

from apps.courses.models import Course
from apps.enrollments.models import Enrollment
from apps.payments.models import BillingDetails, Order, Payment
from apps.payments.services.payment_service import PaymentService
from tests.factories import (
    CourseFactory,
    InstructorFactory,
    OrderFactory,
    PaymentFactory,
    UserFactory,
)


# ──────────────────────────────────────────────
# Fixtures
# ──────────────────────────────────────────────

BILLING = {
    "first_name": "Test",
    "last_name": "Student",
    "email": "student@test.com",
    "country": "Bangladesh",
    "city": "Dhaka",
    "postal_code": "1207",
    "address": "Road 12",
    "phone_number": "+8801000000000",
}


@pytest.fixture
def student(db):
    return UserFactory()


@pytest.fixture
def instructor(db):
    return InstructorFactory()


@pytest.fixture
def paid_course(db, instructor):
    return CourseFactory(
        instructor=instructor,
        status=Course.Status.PUBLISHED,
        is_free=False,
        price=120,
        discount_price=100,
    )


@pytest.fixture
def free_course(db, instructor):
    return CourseFactory(
        instructor=instructor,
        status=Course.Status.PUBLISHED,
        is_free=True,
        price=0,
        discount_price=0,
    )


@pytest.fixture
def draft_course(db, instructor):
    return CourseFactory(
        instructor=instructor,
        status=Course.Status.DRAFT,
        is_free=False,
        price=50,
    )


# ──────────────────────────────────────────────
# create_order
# ──────────────────────────────────────────────


@pytest.mark.django_db
class TestCreateOrder:
    def test_creates_order_and_pending_payment(self, student, paid_course):
        order = PaymentService.create_order(student, paid_course, BILLING)
        assert order.student == student
        assert order.course == paid_course
        assert order.order_status == Order.OrderStatus.PENDING
        assert order.amount == Decimal(str(paid_course.effective_price))
        assert order.payment_method == Order.PaymentMethod.STRIPE
        assert order.payments.count() == 1
        assert order.payments.first().payment_status == Payment.PaymentStatus.PENDING

    def test_order_number_is_unique_per_call(self, student, paid_course):
        course2 = CourseFactory(
            instructor=paid_course.instructor,
            status=Course.Status.PUBLISHED,
            is_free=False,
            price=80,
            discount_price=60,
        )
        order1 = PaymentService.create_order(student, paid_course, BILLING)
        student2 = UserFactory()
        order2 = PaymentService.create_order(student2, course2, {**BILLING, "email": student2.email})
        assert order1.order_number != order2.order_number

    def test_saves_billing_details(self, student, paid_course):
        PaymentService.create_order(student, paid_course, BILLING)
        assert BillingDetails.objects.filter(user=student).exists()
        bd = BillingDetails.objects.get(user=student)
        assert bd.country == "Bangladesh"
        assert bd.city == "Dhaka"

    def test_reject_free_course(self, student, free_course):
        with pytest.raises(ValueError, match="free"):
            PaymentService.create_order(student, free_course, BILLING)

    def test_reject_unpublished_course(self, student, draft_course):
        with pytest.raises(ValueError, match="not published"):
            PaymentService.create_order(student, draft_course, BILLING)

    def test_reject_instructor_purchasing_own_course(self, instructor, paid_course):
        with pytest.raises(ValueError, match="Instructors"):
            PaymentService.create_order(instructor, paid_course, BILLING)

    def test_reject_duplicate_purchase(self, student, paid_course):
        PaymentService.create_order(student, paid_course, BILLING)
        with pytest.raises(ValueError, match="already purchased"):
            PaymentService.create_order(student, paid_course, {**BILLING})

    def test_pending_payment_created_with_empty_payment_data(self, student, paid_course):
        order = PaymentService.create_order(student, paid_course, BILLING)
        payment = order.payments.first()
        assert payment.payment_data == {}


# ──────────────────────────────────────────────
# create_checkout_session
# ──────────────────────────────────────────────


@pytest.mark.django_db
class TestCreateCheckoutSession:
    def test_creates_stripe_checkout_session(self, student, paid_course, monkeypatch):
        order = OrderFactory(
            student=student,
            course=paid_course,
            order_status=Order.OrderStatus.PENDING,
            amount=paid_course.effective_price,
        )
        monkeypatch.setattr(
            "apps.payments.services.payment_service.stripe.checkout.Session.create",
            lambda **kwargs: SimpleNamespace(id="cs_stripe_ok", url="https://stripe.com/cs_stripe_ok"),
        )
        session = PaymentService.create_checkout_session(order)
        assert session.id == "cs_stripe_ok"
        assert session.url == "https://stripe.com/cs_stripe_ok"

    def test_stores_session_id_in_payment_data(self, student, paid_course, monkeypatch):
        order = OrderFactory(
            student=student,
            course=paid_course,
            order_status=Order.OrderStatus.PENDING,
            amount=paid_course.effective_price,
        )
        payment = PaymentFactory(order=order)

        monkeypatch.setattr(
            "apps.payments.services.payment_service.stripe.checkout.Session.create",
            lambda **kwargs: SimpleNamespace(id="cs_data_ok", url="https://stripe.com/cs_data_ok"),
        )

        PaymentService.create_checkout_session(order)
        payment.refresh_from_db()
        assert payment.payment_data["checkout_session_id"] == "cs_data_ok"
        assert payment.payment_data["checkout_url"] == "https://stripe.com/cs_data_ok"

    def test_rejects_non_pending_order(self, student, paid_course):
        order = OrderFactory(
            student=student,
            course=paid_course,
            order_status=Order.OrderStatus.COMPLETED,
            amount=paid_course.effective_price,
        )
        with pytest.raises(ValueError, match="pending"):
            PaymentService.create_checkout_session(order)


# ──────────────────────────────────────────────
# handle_payment_success
# ──────────────────────────────────────────────


@pytest.mark.django_db
class TestHandlePaymentSuccess:
    def test_marks_order_completed_and_payment_success(self, student, paid_course):
        order = OrderFactory(
            student=student,
            course=paid_course,
            order_status=Order.OrderStatus.PENDING,
            amount=paid_course.effective_price,
        )
        PaymentFactory(order=order)

        result = PaymentService.handle_payment_success(order, "pi_ok_123")

        order.refresh_from_db()
        payment = order.payments.first()
        assert result.order_status == Order.OrderStatus.COMPLETED
        assert payment.payment_status == Payment.PaymentStatus.SUCCESS
        assert payment.transaction_id == "pi_ok_123"

    def test_creates_enrollment_after_success(self, student, paid_course):
        order = OrderFactory(
            student=student,
            course=paid_course,
            order_status=Order.OrderStatus.PENDING,
            amount=paid_course.effective_price,
        )
        PaymentFactory(order=order)

        PaymentService.handle_payment_success(order, "pi_enroll_ok")
        assert Enrollment.objects.filter(student=student, course=paid_course).exists()

    def test_idempotent_for_already_completed_order(self, student, paid_course):
        order = OrderFactory(
            student=student,
            course=paid_course,
            order_status=Order.OrderStatus.COMPLETED,
            amount=paid_course.effective_price,
        )
        PaymentFactory(order=order, payment_status=Payment.PaymentStatus.SUCCESS)

        result = PaymentService.handle_payment_success(order, "pi_idempotent")
        assert result.order_status == Order.OrderStatus.COMPLETED

    def test_amount_mismatch_raises_value_error(self, student, paid_course):
        order = OrderFactory(
            student=student,
            course=paid_course,
            order_status=Order.OrderStatus.PENDING,
            amount=Decimal("100.00"),
        )
        PaymentFactory(order=order)

        # amount_received 5000 cents (50 USD) but order is 100 USD
        mismatch_data = {"amount_received": 50_00}
        with pytest.raises(ValueError, match="Amount mismatch"):
            PaymentService.handle_payment_success(order, "pi_bad", payment_data=mismatch_data)

    def test_stores_payment_data_from_stripe(self, student, paid_course):
        order = OrderFactory(
            student=student,
            course=paid_course,
            order_status=Order.OrderStatus.PENDING,
            amount=paid_course.effective_price,
        )
        PaymentFactory(order=order)

        data = {"id": "pi_with_data", "object": "payment_intent", "currency": "usd"}
        PaymentService.handle_payment_success(order, "pi_with_data", payment_data=data)

        payment = order.payments.first()
        payment.refresh_from_db()
        assert payment.payment_data["id"] == "pi_with_data"


# ──────────────────────────────────────────────
# handle_payment_failure
# ──────────────────────────────────────────────


@pytest.mark.django_db
class TestHandlePaymentFailure:
    def test_marks_order_and_payment_failed(self, student, paid_course):
        order = OrderFactory(
            student=student,
            course=paid_course,
            order_status=Order.OrderStatus.PENDING,
            amount=paid_course.effective_price,
        )
        PaymentFactory(order=order)

        result = PaymentService.handle_payment_failure(order, "pi_fail")
        order.refresh_from_db()
        payment = order.payments.first()

        assert result.order_status == Order.OrderStatus.FAILED
        assert payment.payment_status == Payment.PaymentStatus.FAILED
        assert payment.transaction_id == "pi_fail"

    def test_does_not_create_enrollment_on_failure(self, student, paid_course):
        order = OrderFactory(
            student=student,
            course=paid_course,
            order_status=Order.OrderStatus.PENDING,
            amount=paid_course.effective_price,
        )
        PaymentFactory(order=order)

        PaymentService.handle_payment_failure(order, "pi_noenroll")
        assert not Enrollment.objects.filter(student=student, course=paid_course).exists()

    def test_stores_failure_data(self, student, paid_course):
        order = OrderFactory(
            student=student,
            course=paid_course,
            order_status=Order.OrderStatus.PENDING,
            amount=paid_course.effective_price,
        )
        PaymentFactory(order=order)

        failure_data = {"error": {"code": "card_declined", "message": "Card was declined."}}
        PaymentService.handle_payment_failure(order, "pi_declined", payment_data=failure_data)

        payment = order.payments.first()
        payment.refresh_from_db()
        assert payment.payment_data["error"]["code"] == "card_declined"


# ──────────────────────────────────────────────
# refund_order
# ──────────────────────────────────────────────


@pytest.mark.django_db
class TestRefundOrder:
    def test_refunds_completed_order(self, student, paid_course, monkeypatch):
        order = OrderFactory(
            student=student,
            course=paid_course,
            order_status=Order.OrderStatus.COMPLETED,
            amount=paid_course.effective_price,
        )
        payment = PaymentFactory(
            order=order,
            payment_status=Payment.PaymentStatus.SUCCESS,
            transaction_id="pi_to_refund",
        )

        monkeypatch.setattr(
            "apps.payments.services.payment_service.stripe.Refund.create",
            lambda **kwargs: {"id": "re_test", "status": "succeeded"},
        )

        result = PaymentService.refund_order(order)
        order.refresh_from_db()
        payment.refresh_from_db()

        assert result.order_status == Order.OrderStatus.REFUNDED
        assert payment.payment_status == Payment.PaymentStatus.REFUNDED
        assert "refund" in payment.payment_data

    def test_stores_refund_id_in_payment_data(self, student, paid_course, monkeypatch):
        order = OrderFactory(
            student=student,
            course=paid_course,
            order_status=Order.OrderStatus.COMPLETED,
            amount=paid_course.effective_price,
        )
        payment = PaymentFactory(
            order=order,
            payment_status=Payment.PaymentStatus.SUCCESS,
            transaction_id="pi_refund_data",
        )

        monkeypatch.setattr(
            "apps.payments.services.payment_service.stripe.Refund.create",
            lambda **kwargs: {"id": "re_data_ok", "status": "succeeded"},
        )

        PaymentService.refund_order(order)
        payment.refresh_from_db()
        assert payment.payment_data["refund"]["id"] == "re_data_ok"

    def test_reject_refund_on_pending_order(self, student, paid_course):
        order = OrderFactory(
            student=student,
            course=paid_course,
            order_status=Order.OrderStatus.PENDING,
            amount=paid_course.effective_price,
        )
        with pytest.raises(ValueError, match="completed"):
            PaymentService.refund_order(order)

    def test_reject_refund_on_failed_order(self, student, paid_course):
        order = OrderFactory(
            student=student,
            course=paid_course,
            order_status=Order.OrderStatus.FAILED,
            amount=paid_course.effective_price,
        )
        with pytest.raises(ValueError, match="completed"):
            PaymentService.refund_order(order)

    def test_reject_refund_without_transaction_id(self, student, paid_course):
        order = OrderFactory(
            student=student,
            course=paid_course,
            order_status=Order.OrderStatus.COMPLETED,
            amount=paid_course.effective_price,
        )
        PaymentFactory(
            order=order,
            payment_status=Payment.PaymentStatus.SUCCESS,
            transaction_id="",
        )
        with pytest.raises(ValueError, match="transaction"):
            PaymentService.refund_order(order)
