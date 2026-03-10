from django.urls import path, include
from rest_framework.routers import DefaultRouter

from apps.payments import views

router = DefaultRouter()
router.register(r"admin", views.AdminPaymentViewSet, basename="admin-payments")
router.register(r"billing", views.BillingDetailsViewSet, basename="billing-details")

urlpatterns = [
    path("checkout/", views.CheckoutView.as_view(), name="checkout"),
    path("webhook/stripe/", views.StripeWebhookView.as_view(), name="stripe-webhook"),
    path("my/", views.MyPaymentsView.as_view(), name="my-payments"),
    path("", include(router.urls)),
]
