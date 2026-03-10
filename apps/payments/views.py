import stripe
from django.conf import settings
from rest_framework import generics, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.pagination import StandardPagination
from apps.core.permissions import IsAdmin, IsStudent
from apps.courses.models import Course
from apps.enrollments.models import Enrollment
from apps.payments.models import BillingDetails, Payment
from apps.payments.services.payment_service import PaymentService
from apps.payments.serializers import (
    BillingDetailsSerializer,
    CheckoutSerializer,
    PaymentSerializer,
)


class CheckoutView(APIView):
    """
    POST /api/v1/payments/checkout/
    Create a Stripe checkout session for a course.
    """
    permission_classes = [IsAuthenticated, IsStudent]

    def post(self, request):
        serializer = CheckoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            course = Course.objects.get(
                id=serializer.validated_data["course_id"],
                status=Course.Status.PUBLISHED,
            )
        except Course.DoesNotExist:
            return Response(
                {"detail": "Course not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if Enrollment.objects.filter(
            student=request.user, course=course
        ).exists():
            return Response(
                {"detail": "Already enrolled."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        amount = int(course.effective_price * 100)  # cents
        if amount <= 0:
            return Response(
                {"detail": "Course is free. Use enrollment endpoint."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        stripe.api_key = settings.STRIPE_SECRET_KEY

        checkout_session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[
                {
                    "price_data": {
                        "currency": "usd",
                        "unit_amount": amount,
                        "product_data": {
                            "name": course.title,
                        },
                    },
                    "quantity": 1,
                }
            ],
            mode="payment",
            success_url=settings.FRONTEND_URL + "/payment/success?session_id={CHECKOUT_SESSION_ID}",
            cancel_url=settings.FRONTEND_URL + "/payment/failed",
            metadata={
                "user_id": str(request.user.id),
                "course_id": str(course.id),
            },
        )

        PaymentService.create_pending_payment(
            user=request.user,
            course=course,
            checkout_session_id=checkout_session.id,
        )

        return Response(
            {"checkout_url": checkout_session.url},
            status=status.HTTP_201_CREATED,
        )


class StripeWebhookView(APIView):
    """
    POST /api/v1/payments/webhook/stripe/
    Handle Stripe webhook events.
    """
    permission_classes = []
    authentication_classes = []

    def post(self, request):
        payload = request.body
        sig_header = request.META.get("HTTP_STRIPE_SIGNATURE", "")
        webhook_secret = settings.STRIPE_WEBHOOK_SECRET

        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, webhook_secret
            )
        except (ValueError, stripe.error.SignatureVerificationError):
            return Response(status=status.HTTP_400_BAD_REQUEST)

        if event["type"] == "checkout.session.completed":
            session = event["data"]["object"]
            self._handle_checkout_complete(session)

        return Response({"status": "ok"})

    @staticmethod
    def _handle_checkout_complete(session):
        payment = Payment.objects.filter(
            provider_checkout_id=session["id"]
        ).first()
        if not payment:
            return

        PaymentService.complete_checkout_session(
            payment=payment,
            provider_payment_id=session.get("payment_intent", ""),
        )


class MyPaymentsView(generics.ListAPIView):
    """GET /api/v1/payments/my/"""
    serializer_class = PaymentSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardPagination

    def get_queryset(self):
        return Payment.objects.filter(user=self.request.user).select_related("course")


class AdminPaymentViewSet(viewsets.ReadOnlyModelViewSet):
    """
    /api/v1/payments/admin/
    Admin view of all payments.
    """
    serializer_class = PaymentSerializer
    permission_classes = [IsAuthenticated, IsAdmin]
    pagination_class = StandardPagination

    def get_queryset(self):
        qs = Payment.objects.select_related("user", "course")
        payment_status = self.request.query_params.get("status")
        if payment_status:
            qs = qs.filter(status=payment_status)
        return qs


class BillingDetailsViewSet(viewsets.ModelViewSet):
    """
    /api/v1/payments/billing/
    Student CRUD for billing details.
    """
    serializer_class = BillingDetailsSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return BillingDetails.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
