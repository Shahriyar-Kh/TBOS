import uuid
from decimal import Decimal

import stripe
from django.conf import settings
from django.db import IntegrityError, transaction
from django.utils import timezone

from apps.courses.models import Course
from apps.enrollments.services.enrollment_service import EnrollmentService
from apps.payments.models import BillingDetails, Order, Payment


class PaymentService:
    @staticmethod
    def _serialize_gateway_data(payload):
        if payload is None:
            return {}
        if hasattr(payload, "to_dict_recursive"):
            return payload.to_dict_recursive()
        if isinstance(payload, dict):
            return payload
        return {"raw": str(payload)}

    @staticmethod
    def _build_order_number() -> str:
        return f"TBOS-{timezone.now().strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:8].upper()}"

    @staticmethod
    def _upsert_billing_details(user, billing_details: dict) -> BillingDetails:
        return BillingDetails.objects.create(user=user, **billing_details)

    @staticmethod
    def _assert_intent_matches_order(order: Order, payment_intent_data: dict):
        metadata = payment_intent_data.get("metadata") or {}
        intent_order_id = metadata.get("order_id")
        if intent_order_id and str(intent_order_id) != str(order.id):
            raise ValueError("Transaction does not match this order.")

        expected_amount = int(Decimal(str(order.amount)) * 100)
        amount_received = payment_intent_data.get("amount_received")
        if amount_received is not None and int(amount_received) != expected_amount:
            raise ValueError("Amount mismatch detected during payment verification.")

    @staticmethod
    @transaction.atomic
    def create_order(student, course: Course, billing_details: dict) -> Order:
        if course.status != Course.Status.PUBLISHED:
            raise ValueError("Course not found or not published.")
        if course.instructor_id == student.id:
            raise ValueError("Instructors cannot purchase their own course.")
        if course.is_free:
            raise ValueError("Course is free. Use the enrollment endpoint.")

        if Order.objects.filter(student=student, course=course).exists():
            raise ValueError("Course already purchased.")

        amount = Decimal(str(course.effective_price))
        if amount <= Decimal("0"):
            raise ValueError("Invalid order amount for paid checkout.")

        PaymentService._upsert_billing_details(student, billing_details)

        try:
            order = Order.objects.create(
                student=student,
                course=course,
                order_number=PaymentService._build_order_number(),
                order_status=Order.OrderStatus.PENDING,
                amount=amount,
                currency="USD",
                payment_method=Order.PaymentMethod.STRIPE,
            )
        except IntegrityError as exc:
            raise ValueError("Course already purchased.") from exc

        Payment.objects.create(
            order=order,
            payment_provider=Payment.Provider.STRIPE,
            payment_status=Payment.PaymentStatus.PENDING,
            payment_data={},
        )
        return order

    @staticmethod
    @transaction.atomic
    def create_checkout_session(order: Order):
        if order.order_status != Order.OrderStatus.PENDING:
            raise ValueError("Checkout session can only be created for pending orders.")

        stripe.api_key = settings.STRIPE_SECRET_KEY

        unit_amount = int(Decimal(str(order.amount)) * 100)
        if unit_amount <= 0:
            raise ValueError("Invalid payment amount.")

        checkout_session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            mode="payment",
            payment_intent_data={
                "metadata": {
                    "order_id": str(order.id),
                    "order_number": order.order_number,
                }
            },
            line_items=[
                {
                    "price_data": {
                        "currency": order.currency.lower(),
                        "unit_amount": unit_amount,
                        "product_data": {
                            "name": order.course.title,
                        },
                    },
                    "quantity": 1,
                }
            ],
            success_url=settings.FRONTEND_URL + "/payment/success?session_id={CHECKOUT_SESSION_ID}",
            cancel_url=settings.FRONTEND_URL + "/payment/failed",
            client_reference_id=str(order.id),
            metadata={
                "order_id": str(order.id),
                "order_number": order.order_number,
                "student_id": str(order.student_id),
                "course_id": str(order.course_id),
            },
            idempotency_key=f"checkout-{order.order_number}",
        )

        payment = order.payments.order_by("created_at").first()
        if payment:
            payment.payment_data = {
                **(payment.payment_data or {}),
                "checkout_session_id": checkout_session.id,
                "checkout_url": checkout_session.url,
            }
            payment.save(update_fields=["payment_data", "updated_at"])
        return checkout_session

    @staticmethod
    @transaction.atomic
    def verify_payment(order_id, transaction_id: str) -> Order:
        order = Order.objects.select_related("course", "student").get(id=order_id)
        stripe.api_key = settings.STRIPE_SECRET_KEY
        payment_intent = stripe.PaymentIntent.retrieve(transaction_id)
        payment_intent_data = PaymentService._serialize_gateway_data(payment_intent)

        PaymentService._assert_intent_matches_order(order, payment_intent_data)

        if payment_intent.status == "succeeded":
            return PaymentService.handle_payment_success(
                order=order,
                transaction_id=transaction_id,
                payment_data=payment_intent_data,
            )
        return PaymentService.handle_payment_failure(
            order=order,
            transaction_id=transaction_id,
            payment_data=payment_intent_data,
        )

    @staticmethod
    @transaction.atomic
    def handle_payment_success(order: Order, transaction_id: str, payment_data=None) -> Order:
        payment = order.payments.order_by("created_at").first()
        if not payment:
            payment = Payment.objects.create(
                order=order,
                payment_provider=Payment.Provider.STRIPE,
            )

        if order.order_status == Order.OrderStatus.COMPLETED and payment.payment_status == Payment.PaymentStatus.SUCCESS:
            return order

        serialized_payment_data = PaymentService._serialize_gateway_data(payment_data)
        if isinstance(serialized_payment_data, dict):
            PaymentService._assert_intent_matches_order(order, serialized_payment_data)

        payment.transaction_id = transaction_id
        payment.payment_status = Payment.PaymentStatus.SUCCESS
        payment.payment_data = serialized_payment_data
        payment.save(update_fields=["transaction_id", "payment_status", "payment_data", "updated_at"])

        order.order_status = Order.OrderStatus.COMPLETED
        order.save(update_fields=["order_status", "updated_at"])

        PaymentService.enroll_student_after_payment(order)
        return order

    @staticmethod
    @transaction.atomic
    def handle_payment_failure(order: Order, transaction_id: str = "", payment_data=None) -> Order:
        payment = order.payments.order_by("created_at").first()
        if not payment:
            payment = Payment.objects.create(
                order=order,
                payment_provider=Payment.Provider.STRIPE,
            )

        serialized_payment_data = PaymentService._serialize_gateway_data(payment_data)

        payment.transaction_id = transaction_id or payment.transaction_id
        payment.payment_status = Payment.PaymentStatus.FAILED
        payment.payment_data = serialized_payment_data
        payment.save(update_fields=["transaction_id", "payment_status", "payment_data", "updated_at"])

        order.order_status = Order.OrderStatus.FAILED
        order.save(update_fields=["order_status", "updated_at"])
        return order

    @staticmethod
    @transaction.atomic
    def refund_order(order: Order) -> Order:
        if order.order_status != Order.OrderStatus.COMPLETED:
            raise ValueError("Only completed orders can be refunded.")

        payment = order.payments.filter(payment_status=Payment.PaymentStatus.SUCCESS).order_by("-created_at").first()
        if not payment or not payment.transaction_id:
            raise ValueError("Successful payment transaction not found for refund.")

        stripe.api_key = settings.STRIPE_SECRET_KEY
        refund = stripe.Refund.create(payment_intent=payment.transaction_id)

        serialized_refund = PaymentService._serialize_gateway_data(refund)
        payment.payment_status = Payment.PaymentStatus.REFUNDED
        payment.payment_data = {
            **(payment.payment_data or {}),
            "refund": serialized_refund,
        }
        payment.save(update_fields=["payment_status", "payment_data", "updated_at"])

        order.order_status = Order.OrderStatus.REFUNDED
        order.save(update_fields=["order_status", "updated_at"])
        return order

    @staticmethod
    def enroll_student_after_payment(order: Order):
        return EnrollmentService.enroll_paid_course(order.student, order.course)
