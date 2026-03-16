from django.urls import path

from apps.certificates import views

urlpatterns = [
    path("", views.AdminCertificateListView.as_view(), name="admin-certificates"),
    path("<uuid:pk>/", views.AdminCertificateDeleteView.as_view(), name="admin-certificate-delete"),
]
