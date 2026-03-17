"""Tests for Payment API views: checkout, verify, my-orders, order detail, admin, webhook."""
import pytest
from types import SimpleNamespace
from rest_framework import status

from apps.enrollments.models import Enrollment
from apps.payments.models import Order, Payment
from tests.factories import CourseFactory


# ──────────────────────────────────────────────
# Shared helpers
# ──────────────────────────────────────────────

pytestmark = pytest.mark.django_db


def billing_payload(user):
    return {
        "first_name": user.first_name,
        "last_name": user.last_name,
        "email": user.email,
        "country": "Bangladesh",
        "city": "Dhaka",
        "postal_code": "1207",
        "address": "Road 12",
        "phone_number": "+8801000000000",
    }


def paid_course(status="published"):
    return CourseFactory(is_free=False, price=120, discount_price=100, status=status)


def create_pending_order(student, course, order_number="TBOS-TEST-WEB-1"):
    order = Order.objects.create(
        student=student,
        course=course,
        order_number=order_number,
        amount=course.effective_price,
        currency="USD",
        payment_method=Order.PaymentMethod.STRIPE,
        order_status=Order.OrderStatus.PENDING,
    )
    Payment.objects.create(
        order=order,
        payment_provider=Payment.Provider.STRIPE,
        payment_status=Payment.PaymentStatus.PENDING,
    )
    return order


# ──────────────────────────────────────────────
# POST /api/v1/payments/checkout/
# ──────────────────────────────────────────────

class TestCheckoutView:
    def test_free_course_auto_enrolls_and_returns_201(self, auth_client, student_user):
        course = CourseFactory(is_free=True, price=0, discount_price=0, status="published")

        response = auth_client.post(
            "/api/v1/payments/checkout/",
            {"course_id": str(course.id), "billing_details": billing_payload(student_user)},
            format="json",
        )

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["success"] is True
        assert response.data["data"]["is_free"] is True
        assert Enrollment.objects.filter(student=student_user, course=course).exists()

    def test_paid_course_creates_pending_order_and_returns_checkout_url(
        self, auth_client, student_user, monkeypatch
    ):
        course = paid_course()
        monkeypatch.setattr(
            "apps.payments.services.payment_service.stripe.checkout.Session.create",
            lambda **kwargs: SimpleNamespace(id="cs_test_123", url="https://checkout.stripe.com/test"),
        )

        response = auth_client.post(
            "/api/v1/payments/checkout/",
            {"course_id": str(course.id), "billing_details": billing_payload(student_user)},
            format="json",
        )

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["success"] is True
        assert "checkout_url" in response.data["data"]
        assert "order_id" in response.data["data"]

        order = Order.objects.get(student=student_user, course=course)
        assert order.order_status == Order.OrderStatus.PENDING
        payment = Payment.objects.get(order=order)
        assert payment.payment_status == Payment.PaymentStatus.PENDING
        assert payment.payment_data["checkout_session_id"] == "cs_test_123"

    def test_duplicate_purchase_returns_400(self, auth_client, student_user, monkeypatch):
        course = paid_course()
        create_pending_order(student_user, course, order_number="TBOS-WEB-DUP-1")
        monkeypatch.setattr(
            "apps.payments.services.payment_service.stripe.checkout.Session.create",
            lambda **kwargs: SimpleNamespace(id="cs_dup", url="https://checkout.stripe.com/dup"),
        )

        response = auth_client.post(
            "/api/v1/payments/checkout/",
            {"course_id": str(course.id), "billing_details": billing_payload(student_user)},
            format="json",
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data["success"] is False

    def test_nonexistent_course_returns_404(self, auth_client, student_user):
        response = auth_client.post(
            "/api/v1/payments/checkout/",
            {
                "course_id": "00000000-0000-0000-0000-000000000000",
                "billing_details": billing_payload(student_user),
            },
            format="json",
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.data["success"] is False

    def test_unauthenticated_request_returns_401(self, api_client):
        course = paid_course()
        response = api_client.post(
            "/api/v1/payments/checkout/",
            {"course_id": str(course.id), "billing_details": {}},
            format="json",
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_instructor_cannot_checkout(self, instructor_client, instructor_user):
        course = paid_course()
        response = instructor_client.post(
            "/api/v1/payments/checkout/",
            {"course_id": str(course.id), "billing_details": billing_payload(instructor_user)},
            format="json",
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_missing_billing_details_returns_400(self, auth_client, student_user):
        course = paid_course()
        response = auth_client.post(
            "/api/v1/payments/checkout/",
            {"course_id": str(course.id)},
            format="json",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST


# ──────────────────────────────────────────────
# POST /api/v1/payments/verify/
# ──────────────────────────────────────────────

class TestPaymentVerificationView:
    def test_tampered_transaction_order_id_returns_400(self, auth_client, student_user, monkeypatch):
        course = paid_course()
        order = create_pending_order(student_user, course, order_number="TBOS-WEB-VERIFY-1")

        monkeypatch.setattr(
            "apps.payments.services.payment_service.stripe.PaymentIntent.retrieve",
            lambda tx_id: {
                "id": "pi_tamper",
                "status": "succeeded",
                "amount_received": int(order.amount * 100),
                "metadata": {"order_id": "00000000-0000-0000-0000-000000000000"},
            },
        )

        response = auth_client.post(
            "/api/v1/payments/verify/",
            {"order_id": str(order.id), "transaction_id": "pi_tamper"},
            format="json",
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data["success"] is False
        order.refresh_from_db()
        assert order.order_status == Order.OrderStatus.PENDING

    def test_cannot_verify_another_students_order(self, auth_client, student_user):
        other_course = paid_course()
        other_order = create_pending_order(
            other_course.instructor, other_course, order_number="TBOS-WEB-VERIFY-2"
        )

        response = auth_client.post(
            "/api/v1/payments/verify/",
            {"order_id": str(other_order.id), "transaction_id": "pi_other"},
            format="json",
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.data["success"] is False

    def test_verify_nonexistent_order_returns_404(self, auth_client):
        response = auth_client.post(
            "/api/v1/payments/verify/",
            {"order_id": "00000000-0000-0000-0000-000000000000", "transaction_id": "pi_ghost"},
            format="json",
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_unauthenticated_request_returns_401(self, api_client):
        response = api_client.post("/api/v1/payments/verify/", {}, format="json")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


# ──────────────────────────────────────────────
# GET /api/v1/payments/my-orders/
# ──────────────────────────────────────────────

class TestMyOrdersView:
    def test_lists_only_current_student_orders(self, auth_client, student_user):
        my_course = paid_course()
        other_course = CourseFactory(is_free=False, price=140, discount_price=110, status="published")

        my_order = create_pending_order(student_user, my_course, order_number="TBOS-WEB-MY-1")
        create_pending_order(other_course.instructor, other_course, order_number="TBOS-WEB-OTHER-1")

        response = auth_client.get("/api/v1/payments/my-orders/")

        assert response.status_code == status.HTTP_200_OK
        assert response.data["success"] is True
        ids = {row["id"] for row in response.data["data"]["results"]}
        assert str(my_order.id) in ids

    def test_excludes_other_students_orders(self, auth_client, student_user):
        other_course = paid_course()
        create_pending_order(other_course.instructor, other_course, order_number="TBOS-WEB-MY-2")

        response = auth_client.get("/api/v1/payments/my-orders/")
        assert response.data["data"]["count"] == 0

    def test_response_contains_course_info(self, auth_client, student_user):
        course = paid_course()
        create_pending_order(student_user, course, order_number="TBOS-WEB-MY-3")

        response = auth_client.get("/api/v1/payments/my-orders/")

        result = response.data["data"]["results"][0]
        assert result["course"]["id"] == str(course.id)
        assert "amount" in result
        assert "status" in result

    def test_unauthenticated_returns_401(self, api_client):
        response = api_client.get("/api/v1/payments/my-orders/")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_instructor_cannot_access_student_orders(self, instructor_client):
        response = instructor_client.get("/api/v1/payments/my-orders/")
        assert response.status_code == status.HTTP_403_FORBIDDEN


# ──────────────────────────────────────────────
# GET /api/v1/payments/order/{id}/
# ──────────────────────────────────────────────

class TestOrderDetailView:
    def test_returns_own_order_with_payments(self, auth_client, student_user):
        course = paid_course()
        order = create_pending_order(student_user, course, order_number="TBOS-WEB-DETAIL-1")

        response = auth_client.get(f"/api/v1/payments/order/{order.id}/")

        assert response.status_code == status.HTTP_200_OK
        assert response.data["success"] is True
        data = response.data["data"]
        assert data["id"] == str(order.id)
        assert "payments" in data

    def test_cannot_view_another_students_order(self, auth_client, student_user):
        course = paid_course()
        other_order = create_pending_order(
            course.instructor, course, order_number="TBOS-WEB-DETAIL-2"
        )

        response = auth_client.get(f"/api/v1/payments/order/{other_order.id}/")

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.data["success"] is False

    def test_nonexistent_order_returns_404(self, auth_client):
        response = auth_client.get("/api/v1/payments/order/00000000-0000-0000-0000-000000000000/")
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_unauthenticated_returns_401(self, api_client):
        course = paid_course()
        order = create_pending_order(CourseFactory().instructor, course, order_number="TBOS-WEB-DETAIL-3")
        response = api_client.get(f"/api/v1/payments/order/{order.id}/")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


# ──────────────────────────────────────────────
# GET /api/v1/admin/payments/
# ──────────────────────────────────────────────

class TestAdminPaymentsListView:
    def test_admin_can_list_all_payments(self, admin_client, student_user):
        course = paid_course()
        order = create_pending_order(student_user, course, order_number="TBOS-WEB-ADM-1")

        response = admin_client.get("/api/v1/admin/payments/")

        assert response.status_code == status.HTTP_200_OK
        assert response.data["success"] is True
        ids = {row["id"] for row in response.data["data"]["results"]}
        assert str(order.payments.first().id) in ids

    def test_student_cannot_access_admin_endpoint(self, auth_client):
        response = auth_client.get("/api/v1/admin/payments/")
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_instructor_cannot_access_admin_endpoint(self, instructor_client):
        response = instructor_client.get("/api/v1/admin/payments/")
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_unauthenticated_returns_401(self, api_client):
        response = api_client.get("/api/v1/admin/payments/")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_filter_by_payment_status(self, admin_client, student_user):
        course = paid_course()
        order = create_pending_order(student_user, course, order_number="TBOS-WEB-ADM-FILTER")
        payment = order.payments.first()
        payment.payment_status = Payment.PaymentStatus.SUCCESS
        payment.save(update_fields=["payment_status", "updated_at"])

        response = admin_client.get("/api/v1/admin/payments/", {"status": "SUCCESS"})

        assert response.status_code == status.HTTP_200_OK
        ids = {row["id"] for row in response.data["data"]["results"]}
        assert str(payment.id) in ids


# ──────────────────────────────────────────────
# POST /api/v1/admin/payments/refund/
# ──────────────────────────────────────────────

class TestAdminRefundOrderView:
    def test_admin_can_refund_completed_order(self, admin_client, student_user, monkeypatch):
        course = paid_course()
        order = create_pending_order(student_user, course, order_number="TBOS-WEB-REFUND-1")
        payment = order.payments.first()
        order.order_status = Order.OrderStatus.COMPLETED
        order.save(update_fields=["order_status", "updated_at"])
        payment.payment_status = Payment.PaymentStatus.SUCCESS
        payment.transaction_id = "pi_refund_ok"
        payment.save(update_fields=["payment_status", "transaction_id", "updated_at"])

        monkeypatch.setattr(
            "apps.payments.services.payment_service.stripe.Refund.create",
            lambda **kwargs: {"id": "re_test_1", "status": "succeeded"},
        )

        response = admin_client.post(
            "/api/v1/admin/payments/refund/",
            {"order_id": str(order.id)},
            format="json",
        )

        order.refresh_from_db()
        payment.refresh_from_db()

        assert response.status_code == status.HTTP_200_OK
        assert response.data["success"] is True
        assert order.order_status == Order.OrderStatus.REFUNDED
        assert payment.payment_status == Payment.PaymentStatus.REFUNDED

    def test_refund_response_contains_order_detail(self, admin_client, student_user, monkeypatch):
        course = paid_course()
        order = create_pending_order(student_user, course, order_number="TBOS-WEB-REFUND-RESP")
        payment = order.payments.first()
        order.order_status = Order.OrderStatus.COMPLETED
        order.save(update_fields=["order_status", "updated_at"])
        payment.payment_status = Payment.PaymentStatus.SUCCESS
        payment.transaction_id = "pi_resp_ok"
        payment.save(update_fields=["payment_status", "transaction_id", "updated_at"])

        monkeypatch.setattr(
            "apps.payments.services.payment_service.stripe.Refund.create",
            lambda **kwargs: {"id": "re_resp_ok", "status": "succeeded"},
        )

        response = admin_client.post(
            "/api/v1/admin/payments/refund/",
            {"order_id": str(order.id)},
            format="json",
        )

        data = response.data["data"]
        assert data["id"] == str(order.id)
        assert data["status"] == Order.OrderStatus.REFUNDED

    def test_refund_pending_order_returns_400(self, admin_client, student_user):
        course = paid_course()
        order = create_pending_order(student_user, course, order_number="TBOS-WEB-REFUND-PEND")

        response = admin_client.post(
            "/api/v1/admin/payments/refund/",
            {"order_id": str(order.id)},
            format="json",
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data["success"] is False

    def test_refund_nonexistent_order_returns_404(self, admin_client):
        response = admin_client.post(
            "/api/v1/admin/payments/refund/",
            {"order_id": "00000000-0000-0000-0000-000000000000"},
            format="json",
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_student_cannot_access_refund_endpoint(self, auth_client, student_user):
        course = paid_course()
        order = create_pending_order(student_user, course, order_number="TBOS-WEB-REFUND-AUTH")

        response = auth_client.post(
            "/api/v1/admin/payments/refund/",
            {"order_id": str(order.id)},
            format="json",
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN


# ──────────────────────────────────────────────
# POST /api/v1/payments/stripe-webhook/
# ──────────────────────────────────────────────

class TestStripeWebhookView:
    def test_checkout_session_completed_marks_order_completed_and_enrolls(
        self, api_client, student_user
    ):
        course = paid_course()
        order = create_pending_order(student_user, course, order_number="TBOS-WEB-WH-1")

        event = {
            "type": "checkout.session.completed",
            "data": {
                "object": {
                    "id": "cs_test_123",
                    "payment_intent": "pi_test_123",
                    "metadata": {"order_id": str(order.id)},
                    "amount_total": int(order.amount * 100),
                }
            },
        }

        with pytest.MonkeyPatch.context() as mp:
            mp.setattr(
                "apps.payments.views.stripe.Webhook.construct_event",
                lambda payload, sig_header, secret: event,
            )
            response = api_client.post("/api/v1/payments/stripe-webhook/", data={}, format="json")

        order.refresh_from_db()
        payment = order.payments.first()

        assert response.status_code == status.HTTP_200_OK
        assert order.order_status == Order.OrderStatus.COMPLETED
        assert payment.payment_status == Payment.PaymentStatus.SUCCESS
        assert Enrollment.objects.filter(student=student_user, course=course).exists()

    def test_checkout_amount_mismatch_marks_order_failed_no_enrollment(
        self, api_client, student_user
    ):
        course = paid_course()
        order = create_pending_order(student_user, course, order_number="TBOS-WEB-WH-2")

        event = {
            "type": "checkout.session.completed",
            "data": {
                "object": {
                    "id": "cs_test_999",
                    "payment_intent": "pi_test_999",
                    "metadata": {"order_id": str(order.id)},
                    "amount_total": int(order.amount * 100) + 500,  # tampered amount
                }
            },
        }

        with pytest.MonkeyPatch.context() as mp:
            mp.setattr(
                "apps.payments.views.stripe.Webhook.construct_event",
                lambda payload, sig_header, secret: event,
            )
            response = api_client.post("/api/v1/payments/stripe-webhook/", data={}, format="json")

        order.refresh_from_db()
        payment = order.payments.first()

        assert response.status_code == status.HTTP_200_OK
        assert order.order_status == Order.OrderStatus.FAILED
        assert payment.payment_status == Payment.PaymentStatus.FAILED
        assert not Enrollment.objects.filter(student=student_user, course=course).exists()

    def test_payment_intent_succeeded_event_enrolls_student(self, api_client, student_user):
        course = paid_course()
        order = create_pending_order(student_user, course, order_number="TBOS-WEB-WH-3")

        event = {
            "type": "payment_intent.succeeded",
            "data": {
                "object": {
                    "id": "pi_intent_ok",
                    "metadata": {"order_id": str(order.id)},
                    "amount_received": int(order.amount * 100),
                }
            },
        }

        with pytest.MonkeyPatch.context() as mp:
            mp.setattr(
                "apps.payments.views.stripe.Webhook.construct_event",
                lambda payload, sig_header, secret: event,
            )
            api_client.post("/api/v1/payments/stripe-webhook/", data={}, format="json")

        order.refresh_from_db()
        assert order.order_status == Order.OrderStatus.COMPLETED
        assert Enrollment.objects.filter(student=student_user, course=course).exists()

    def test_payment_intent_failed_event_marks_order_failed(self, api_client, student_user):
        course = paid_course()
        order = create_pending_order(student_user, course, order_number="TBOS-WEB-WH-4")

        event = {
            "type": "payment_intent.payment_failed",
            "data": {
                "object": {
                    "id": "pi_intent_fail",
                    "metadata": {"order_id": str(order.id)},
                }
            },
        }

        with pytest.MonkeyPatch.context() as mp:
            mp.setattr(
                "apps.payments.views.stripe.Webhook.construct_event",
                lambda payload, sig_header, secret: event,
            )
            api_client.post("/api/v1/payments/stripe-webhook/", data={}, format="json")

        order.refresh_from_db()
        assert order.order_status == Order.OrderStatus.FAILED
        assert not Enrollment.objects.filter(student=student_user, course=course).exists()

    def test_invalid_stripe_signature_returns_400(self, api_client):
        with pytest.MonkeyPatch.context() as mp:
            mp.setattr(
                "apps.payments.views.stripe.Webhook.construct_event",
                lambda payload, sig_header, secret: (_ for _ in ()).throw(ValueError("invalid")),
            )
            response = api_client.post("/api/v1/payments/stripe-webhook/", data={}, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data["success"] is False

    def test_unknown_event_type_returns_200(self, api_client):
        event = {"type": "some.unknown.event", "data": {"object": {}}}

        with pytest.MonkeyPatch.context() as mp:
            mp.setattr(
                "apps.payments.views.stripe.Webhook.construct_event",
                lambda payload, sig_header, secret: event,
            )
            response = api_client.post("/api/v1/payments/stripe-webhook/", data={}, format="json")

        assert response.status_code == status.HTTP_200_OK
        assert response.data["data"]["event_type"] == "some.unknown.event"

    def test_webhook_without_order_metadata_is_ignored_gracefully(self, api_client):
        event = {
            "type": "checkout.session.completed",
            "data": {
                "object": {
                    "id": "cs_no_meta",
                    "payment_intent": "pi_no_meta",
                    "metadata": {},
                    "amount_total": 10000,
                }
            },
        }

        with pytest.MonkeyPatch.context() as mp:
            mp.setattr(
                "apps.payments.views.stripe.Webhook.construct_event",
                lambda payload, sig_header, secret: event,
            )
            response = api_client.post("/api/v1/payments/stripe-webhook/", data={}, format="json")

        assert response.status_code == status.HTTP_200_OK
