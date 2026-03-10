from django.urls import path

from apps.notifications import views

urlpatterns = [
    path("", views.MyNotificationsView.as_view(), name="my-notifications"),
    path("unread-count/", views.UnreadCountView.as_view(), name="unread-count"),
    path("<uuid:pk>/read/", views.MarkReadView.as_view(), name="mark-read"),
    path("mark-all-read/", views.MarkAllReadView.as_view(), name="mark-all-read"),
    path(
        "admin/bulk/",
        views.AdminBulkNotificationView.as_view(),
        name="admin-bulk-notification",
    ),
]
