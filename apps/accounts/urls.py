from django.urls import path, include
from rest_framework.routers import DefaultRouter

from apps.accounts import views

router = DefaultRouter()
router.register(r"admin/users", views.AdminUserViewSet, basename="admin-users")

urlpatterns = [
    path("register/", views.RegisterView.as_view(), name="register"),
    path("login/", views.LoginView.as_view(), name="login"),
    path("token/refresh/", views.TokenRefresh.as_view(), name="token-refresh"),
    path("me/", views.MeView.as_view(), name="me"),
    path(
        "change-password/",
        views.ChangePasswordView.as_view(),
        name="change-password",
    ),
    path("", include(router.urls)),
]
