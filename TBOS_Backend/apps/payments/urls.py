from django.urls import path

from apps.payments import views

urlpatterns = [
    path("checkout/", views.CheckoutView.as_view(), name="checkout"),
    path("verify/", views.PaymentVerificationView.as_view(), name="payment-verify"),
    path("my-orders/", views.MyOrdersView.as_view(), name="my-orders"),
    path("order/<uuid:pk>/", views.OrderDetailView.as_view(), name="order-detail"),
    path("stripe-webhook/", views.StripeWebhookView.as_view(), name="stripe-webhook"),
]
