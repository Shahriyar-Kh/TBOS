from django.contrib.auth import get_user_model
from rest_framework import generics, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.pagination import StandardPagination
from apps.core.permissions import IsAdmin
from apps.notifications.models import Notification
from apps.notifications.services.notification_service import NotificationService
from apps.notifications.serializers import (
    BulkNotificationSerializer,
    NotificationSerializer,
)

User = get_user_model()


class MyNotificationsView(generics.ListAPIView):
    """
    GET /api/v1/notifications/
    List notifications for the authenticated user.
    """
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardPagination

    def get_queryset(self):
        qs = Notification.objects.filter(recipient=self.request.user)
        is_read = self.request.query_params.get("is_read")
        if is_read is not None:
            qs = qs.filter(is_read=is_read.lower() == "true")
        return qs


class UnreadCountView(APIView):
    """
    GET /api/v1/notifications/unread-count/
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        count = Notification.objects.filter(
            recipient=request.user, is_read=False
        ).count()
        return Response({"unread_count": count})


class MarkReadView(APIView):
    """
    POST /api/v1/notifications/{id}/read/
    Mark a single notification as read.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        notification = Notification.objects.filter(
            id=pk, recipient=request.user
        ).first()
        if not notification:
            return Response(
                {"detail": "Notification not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        NotificationService.mark_read(notification)
        return Response({"success": True})


class MarkAllReadView(APIView):
    """
    POST /api/v1/notifications/mark-all-read/
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        NotificationService.mark_all_read(request.user)
        return Response({"success": True})


class AdminBulkNotificationView(APIView):
    """
    POST /api/v1/notifications/admin/bulk/
    Send a notification to all users or a specific role.
    """
    permission_classes = [IsAuthenticated, IsAdmin]

    def post(self, request):
        serializer = BulkNotificationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        target_role = data.pop("target_role")
        users = User.objects.filter(is_active=True)
        if target_role != "all":
            users = users.filter(role=target_role)

        notifications = NotificationService.bulk_notify(
            recipients=users,
            notification_type=data["notification_type"],
            title=data["title"],
            message=data["message"],
            action_url=data.get("action_url", ""),
        )

        return Response(
            {
                "success": True,
                "sent_to": len(notifications),
            },
            status=status.HTTP_201_CREATED,
        )
