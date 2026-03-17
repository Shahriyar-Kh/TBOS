from django.urls import path

from apps.payments import views

urlpatterns = [
    path("", views.AdminPaymentsListView.as_view(), name="admin-payments"),
    path("refund/", views.AdminRefundOrderView.as_view(), name="admin-payments-refund"),
]
