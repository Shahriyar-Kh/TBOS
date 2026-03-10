from django.urls import path

from apps.certificates import views

urlpatterns = [
    path("my/", views.MyCertificatesView.as_view(), name="my-certificates"),
    path("request/", views.RequestCertificateView.as_view(), name="request-certificate"),
    path("verify/", views.VerifyCertificateView.as_view(), name="verify-certificate"),
    path("admin/", views.AdminCertificateListView.as_view(), name="admin-certificates"),
]
