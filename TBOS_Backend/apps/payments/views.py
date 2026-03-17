import stripe
from django.conf import settings
from django.db.models import Prefetch
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiExample, OpenApiParameter, extend_schema, inline_serializer
from rest_framework import status
from rest_framework import serializers
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from apps.core.api_docs import (
    AUTH_GUIDE,
    COURSE_PARAM,
    PAGE_PARAM,
    PAGE_SIZE_PARAM,
    ROLE_ACCESS_GUIDE,
    STATUS_PARAM,
    START_DATE_PARAM,
    END_DATE_PARAM,
    PAYMENT_EXAMPLE,
    standard_error_responses,
    success_example,
    success_response,
)
from apps.core.exceptions import api_error, api_success
from apps.core.pagination import StandardPagination
from apps.core.permissions import IsAdmin, IsStudent
from apps.courses.models import Course
from apps.enrollments.services.enrollment_service import EnrollmentService
from apps.payments.models import Order, Payment
from apps.payments.serializers import (
    CheckoutSerializer,
    OrderDetailSerializer,
    OrderSerializer,
    PaymentSerializer,
    PaymentVerificationSerializer,
    RefundOrderSerializer,
)
from apps.payments.services.payment_service import PaymentService


class CheckoutView(APIView):
    permission_classes = [IsAuthenticated, IsStudent]

    @extend_schema(
        tags=["Payments"],
        summary="Create checkout session",
        description=f"Create a checkout session for paid courses or immediate enrollment for free courses.\n\n{AUTH_GUIDE}",
        request=CheckoutSerializer,
        responses={
            201: success_response("CheckoutResponse", None),
            **standard_error_responses(400, 401, 403, 404, 500),
        },
    )
    def post(self, request):
        serializer = CheckoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            course = Course.objects.get(
                id=serializer.validated_data["course_id"],
                status=Course.Status.PUBLISHED,
            )
        except Course.DoesNotExist:
            return api_error(
                message="Course not found.",
                errors={"course_id": "Course not found."},
                status_code=status.HTTP_404_NOT_FOUND,
            )

        if EnrollmentService.check_enrollment_access(request.user, course):
            return api_error(
                message="Course already purchased.",
                errors={"course": "Course already purchased."},
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        if course.is_free:
            enrollment = EnrollmentService.enroll_student(request.user, course)
            return api_success(
                data={
                    "course_id": str(course.id),
                    "enrollment_id": str(enrollment.id),
                    "is_free": True,
                },
                message="Free course enrolled successfully.",
                status_code=status.HTTP_201_CREATED,
            )

        try:
            order = PaymentService.create_order(
                student=request.user,
                course=course,
                billing_details=serializer.validated_data["billing_details"],
            )
            checkout_session = PaymentService.create_checkout_session(order)
        except ValueError as exc:
            return api_error(
                message=str(exc),
                errors={"detail": str(exc)},
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        return api_success(
            data={
                "order_id": str(order.id),
                "order_number": order.order_number,
                "checkout_url": checkout_session.url,
                "checkout_session_id": checkout_session.id,
            },
            message="Checkout session created successfully.",
            status_code=status.HTTP_201_CREATED,
        )


class PaymentVerificationView(APIView):
    permission_classes = [IsAuthenticated, IsStudent]

    @extend_schema(
        tags=["Payments"],
        summary="Verify payment transaction",
        request=PaymentVerificationSerializer,
        responses={200: success_response("PaymentVerifyResponse", OrderDetailSerializer), **standard_error_responses(400, 401, 403, 404, 500)},
    )
    def post(self, request):
        serializer = PaymentVerificationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            order = Order.objects.get(id=serializer.validated_data["order_id"], student=request.user)
        except Order.DoesNotExist:
            return api_error(
                message="Order not found.",
                errors={"order_id": "Order not found."},
                status_code=status.HTTP_404_NOT_FOUND,
            )

        try:
            order = PaymentService.verify_payment(
                order_id=order.id,
                transaction_id=serializer.validated_data["transaction_id"],
            )
        except ValueError as exc:
            return api_error(
                message=str(exc),
                errors={"detail": str(exc)},
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        return api_success(
            data=OrderDetailSerializer(order).data,
            message="Payment verification completed.",
        )


class MyOrdersView(APIView):
    permission_classes = [IsAuthenticated, IsStudent]
    pagination_class = StandardPagination

    @extend_schema(
        tags=["Payments"],
        summary="List student orders",
        parameters=[PAGE_PARAM, PAGE_SIZE_PARAM],
        responses={200: success_response("MyOrdersResponse", None), **standard_error_responses(401, 403, 500)},
    )
    def get(self, request):
        queryset = (
            Order.objects.filter(student=request.user)
            .select_related("course", "course__category", "course__level", "course__instructor")
            .prefetch_related("payments")
            .order_by("-created_at")
        )

        paginator = self.pagination_class()
        page = paginator.paginate_queryset(queryset, request, view=self)
        serializer = OrderSerializer(page, many=True)
        return api_success(
            data={
                "page": paginator.page.number,
                "page_size": paginator.get_page_size(request) or paginator.page_size,
                "total_count": paginator.page.paginator.count,
                "count": paginator.page.paginator.count,
                "next": paginator.get_next_link(),
                "previous": paginator.get_previous_link(),
                "results": serializer.data,
            },
            message="Orders retrieved successfully.",
        )


class OrderDetailView(APIView):
    permission_classes = [IsAuthenticated, IsStudent]

    @extend_schema(
        tags=["Payments"],
        summary="Get order details",
        responses={200: success_response("OrderDetailResponse", OrderDetailSerializer), **standard_error_responses(401, 403, 404, 500)},
    )
    def get(self, request, pk):
        order = (
            Order.objects.filter(student=request.user, id=pk)
            .select_related("course", "course__category", "course__level", "course__instructor")
            .prefetch_related("payments")
            .first()
        )
        if not order:
            return api_error(
                message="Order not found.",
                errors={"order": "Order not found."},
                status_code=status.HTTP_404_NOT_FOUND,
            )
        return api_success(
            data=OrderDetailSerializer(order).data,
            message="Order details retrieved successfully.",
        )


class StripeWebhookView(APIView):
    permission_classes = []
    authentication_classes = []

    @extend_schema(
        tags=["Payments"],
        summary="Stripe webhook receiver",
        description=(
            "Receive Stripe events for payment lifecycle updates. The request must include the `Stripe-Signature` header, "
            "and payload integrity is validated using the configured webhook secret.\n\n"
            "Supported events: `checkout.session.completed`, `payment_intent.succeeded`, `payment_intent.payment_failed`."
        ),
        parameters=[
            OpenApiParameter(
                name="Stripe-Signature",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.HEADER,
                required=True,
                description="Stripe signature used for webhook verification.",
            )
        ],
        request=inline_serializer(
            name="StripeWebhookPayload",
            fields={
                "id": serializers.CharField(),
                "type": serializers.CharField(),
                "data": serializers.JSONField(),
            },
        ),
        examples=[OpenApiExample("StripeCheckoutCompleted", value={"id": "evt_1Qw...", "type": "checkout.session.completed", "data": {"object": {"id": "cs_test_123", "payment_intent": "pi_123", "metadata": {"order_id": "bbf3e5b9-7b26-4294-b4ce-3fa6cc786f6b"}}}}, request_only=True)],
        responses={200: success_response("StripeWebhookResponse", None), **standard_error_responses(400, 500)},
        auth=[],
    )
    def post(self, request):
        payload = request.body
        signature = request.META.get("HTTP_STRIPE_SIGNATURE", "")

        try:
            event = stripe.Webhook.construct_event(
                payload=payload,
                sig_header=signature,
                secret=settings.STRIPE_WEBHOOK_SECRET,
            )
        except (ValueError, stripe.error.SignatureVerificationError):
            return api_error(
                message="Invalid webhook payload.",
                errors={"detail": "Invalid signature or payload."},
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        event_type = event.get("type")
        data = event.get("data", {}).get("object", {})

        if event_type == "checkout.session.completed":
            self._on_checkout_session_completed(data)
        elif event_type == "payment_intent.succeeded":
            self._on_payment_intent_succeeded(data)
        elif event_type == "payment_intent.payment_failed":
            self._on_payment_intent_failed(data)

        return api_success(
            data={"event_type": event_type},
            message="Webhook processed.",
        )

    @staticmethod
    def _resolve_order_from_data(data):
        metadata = data.get("metadata") or {}
        order_id = metadata.get("order_id") or data.get("client_reference_id")
        if not order_id:
            return None
        return Order.objects.filter(id=order_id).select_related("student", "course").first()

    @classmethod
    def _on_checkout_session_completed(cls, session):
        order = cls._resolve_order_from_data(session)
        if not order:
            return

        amount_total = session.get("amount_total")
        expected = int(order.amount * 100)
        if amount_total is not None and int(amount_total) != expected:
            PaymentService.handle_payment_failure(
                order=order,
                transaction_id=session.get("payment_intent", ""),
                payment_data=session,
            )
            return

        PaymentService.handle_payment_success(
            order=order,
            transaction_id=session.get("payment_intent", ""),
            payment_data=session,
        )

    @classmethod
    def _on_payment_intent_succeeded(cls, payment_intent):
        order = cls._resolve_order_from_data(payment_intent)
        if not order:
            return
        try:
            PaymentService.handle_payment_success(
                order=order,
                transaction_id=payment_intent.get("id", ""),
                payment_data=payment_intent,
            )
        except ValueError:
            PaymentService.handle_payment_failure(
                order=order,
                transaction_id=payment_intent.get("id", ""),
                payment_data=payment_intent,
            )

    @classmethod
    def _on_payment_intent_failed(cls, payment_intent):
        order = cls._resolve_order_from_data(payment_intent)
        if not order:
            return
        PaymentService.handle_payment_failure(
            order=order,
            transaction_id=payment_intent.get("id", ""),
            payment_data=payment_intent,
        )


class AdminPaymentsListView(APIView):
    permission_classes = [IsAuthenticated, IsAdmin]
    pagination_class = StandardPagination

    @extend_schema(
        tags=["Payments"],
        summary="List all payments",
        description=f"Administrative payment ledger view.\n\n{AUTH_GUIDE}\n\n{ROLE_ACCESS_GUIDE}",
        parameters=[PAGE_PARAM, PAGE_SIZE_PARAM, STATUS_PARAM],
        responses={200: success_response("AdminPaymentsListResponse", None), **standard_error_responses(401, 403, 500)},
    )
    def get(self, request):
        queryset = (
            Payment.objects.select_related("order", "order__student", "order__course")
            .prefetch_related(
                Prefetch(
                    "order__payments",
                    queryset=Payment.objects.order_by("-created_at"),
                )
            )
            .order_by("-created_at")
        )
        status_filter = request.query_params.get("status")
        if status_filter:
            queryset = queryset.filter(payment_status=status_filter)

        paginator = self.pagination_class()
        page = paginator.paginate_queryset(queryset, request, view=self)
        serializer = PaymentSerializer(page, many=True)

        return api_success(
            data={
                "page": paginator.page.number,
                "page_size": paginator.get_page_size(request) or paginator.page_size,
                "total_count": paginator.page.paginator.count,
                "count": paginator.page.paginator.count,
                "next": paginator.get_next_link(),
                "previous": paginator.get_previous_link(),
                "results": serializer.data,
            },
            message="Payments retrieved successfully.",
        )


class AdminRefundOrderView(APIView):
    permission_classes = [IsAuthenticated, IsAdmin]

    @extend_schema(
        tags=["Payments"],
        summary="Refund order",
        request=RefundOrderSerializer,
        responses={200: success_response("AdminRefundResponse", OrderDetailSerializer), **standard_error_responses(400, 401, 403, 404, 500)},
    )
    def post(self, request):
        serializer = RefundOrderSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        order = Order.objects.filter(id=serializer.validated_data["order_id"]).select_related("student", "course").first()
        if not order:
            return api_error(
                message="Order not found.",
                errors={"order_id": "Order not found."},
                status_code=status.HTTP_404_NOT_FOUND,
            )

        try:
            refunded_order = PaymentService.refund_order(order)
        except ValueError as exc:
            return api_error(
                message=str(exc),
                errors={"detail": str(exc)},
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        return api_success(
            data=OrderDetailSerializer(refunded_order).data,
            message="Order refunded successfully.",
        )
