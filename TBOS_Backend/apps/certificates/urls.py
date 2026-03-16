from django.urls import path

from apps.certificates import views

urlpatterns = [
    path("my/", views.MyCertificatesView.as_view(), name="my-certificates"),
    path("<uuid:pk>/download/", views.CertificateDownloadView.as_view(), name="certificate-download"),
    path(
        "verify/<str:verification_code>/",
        views.VerifyCertificateView.as_view(),
        name="verify-certificate",
    ),
]
