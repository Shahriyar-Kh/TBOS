from django.conf import settings
from django.db import transaction

from apps.courses.models import Course
from apps.enrollments.models import Enrollment
from apps.payments.models import Payment


class PaymentService:
    @staticmethod
    def create_pending_payment(user, course: Course, checkout_session_id: str) -> Payment:
        return Payment.objects.create(
            user=user,
            course=course,
            amount=course.effective_price,
            provider=Payment.Provider.STRIPE,
            provider_checkout_id=checkout_session_id,
            status=Payment.Status.PENDING,
        )

    @staticmethod
    @transaction.atomic
    def create_payment(user, course: Course, provider_payment_id: str, amount=None) -> Payment:
        payment = Payment.objects.create(
            user=user,
            course=course,
            amount=amount or course.price,
            provider=Payment.Provider.STRIPE,
            provider_payment_id=provider_payment_id,
            status=Payment.Status.COMPLETED,
        )

        Enrollment.objects.get_or_create(student=user, course=course)
        course.total_enrollments = course.enrollments.count()
        course.save(update_fields=["total_enrollments"])

        return payment

    @staticmethod
    def mark_failed(payment: Payment, reason: str = "") -> Payment:
        payment.status = Payment.Status.FAILED
        payment.save(update_fields=["status", "updated_at"])
        return payment

    @staticmethod
    @transaction.atomic
    def complete_checkout_session(payment: Payment, provider_payment_id: str = "") -> Payment:
        payment.provider_payment_id = provider_payment_id
        payment.status = Payment.Status.COMPLETED
        payment.save(update_fields=["provider_payment_id", "status", "updated_at"])

        Enrollment.objects.get_or_create(student=payment.user, course=payment.course)

        if payment.course:
            payment.course.total_enrollments = payment.course.enrollments.filter(
                is_active=True
            ).count()
            payment.course.save(update_fields=["total_enrollments"])

        return payment

    @staticmethod
    @transaction.atomic
    def process_refund(payment: Payment) -> Payment:
        payment.status = Payment.Status.REFUNDED
        payment.save(update_fields=["status", "updated_at"])
        return payment
