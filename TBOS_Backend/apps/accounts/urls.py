from django.urls import path

from apps.accounts import views

urlpatterns = [
    path("auth/register/", views.RegisterView.as_view(), name="register"),
    path("auth/login/", views.LoginView.as_view(), name="login"),
    path("auth/google-login/", views.GoogleLoginView.as_view(), name="google-login"),
    path("auth/logout/", views.LogoutView.as_view(), name="logout"),
    path("auth/me/", views.MeView.as_view(), name="me"),
    path("auth/profile/", views.ProfileView.as_view(), name="profile"),
    path("auth/profile/update/", views.ProfileUpdateView.as_view(), name="profile-update"),
    path(
        "auth/change-password/",
        views.ChangePasswordView.as_view(),
        name="change-password",
    ),
    path("admin/users/", views.AdminUsersView.as_view(), name="admin-users"),
    path("admin/instructors/", views.AdminInstructorsView.as_view(), name="admin-instructors"),
    path("admin/students/", views.AdminStudentsView.as_view(), name="admin-students"),
    path("admin/users/<uuid:user_id>/<str:action>/", views.AdminUserStatusView.as_view(), name="admin-user-status"),
]
