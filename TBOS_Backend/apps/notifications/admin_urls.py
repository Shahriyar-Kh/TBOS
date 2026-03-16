from django.urls import path

from apps.notifications.views import AdminBroadcastNotificationView


urlpatterns = [
    path("broadcast/", AdminBroadcastNotificationView.as_view(), name="admin-notification-broadcast"),
]