from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from apps.core.exceptions import api_error, api_success
from apps.core.pagination import StandardPagination
from apps.core.permissions import IsAdmin
from apps.notifications.services.notification_service import NotificationService
from apps.notifications.serializers import (
    BroadcastNotificationSerializer,
    NotificationSerializer,
    NotificationPreferenceSerializer,
)


class NotificationListView(APIView):
    permission_classes = [IsAuthenticated]
    pagination_class = StandardPagination

    def get(self, request):
        is_read_param = request.query_params.get("is_read")
        is_read = None
        if is_read_param is not None:
            is_read = is_read_param.lower() == "true"

        queryset = NotificationService.get_user_notifications(user=request.user, is_read=is_read)
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(queryset, request, view=self)
        serializer = NotificationSerializer(page, many=True)
        return api_success(
            data={
                "count": paginator.page.paginator.count,
                "next": paginator.get_next_link(),
                "previous": paginator.get_previous_link(),
                "results": serializer.data,
            },
            message="Notifications retrieved.",
        )


class NotificationReadView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request, pk):
        notification = NotificationService.mark_notification_read(
            notification_id=pk,
            user=request.user,
        )
        if not notification:
            return api_error(
                message="Notification not found.",
                status_code=status.HTTP_404_NOT_FOUND,
            )
        return api_success(
            data=NotificationSerializer(notification).data,
            message="Notification marked as read.",
        )


class NotificationReadAllView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request):
        updated_count = NotificationService.mark_all_notifications_read(user=request.user)
        return api_success(
            data={"updated_count": updated_count},
            message="All notifications marked as read.",
        )


class NotificationPreferenceView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        preference = NotificationService.get_or_create_preferences(request.user)
        serializer = NotificationPreferenceSerializer(preference)
        return api_success(
            data=serializer.data,
            message="Notification preferences retrieved.",
        )

    def put(self, request):
        preference = NotificationService.get_or_create_preferences(request.user)
        serializer = NotificationPreferenceSerializer(preference, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return api_success(
            data=serializer.data,
            message="Notification preferences updated.",
        )


class AdminBroadcastNotificationView(APIView):
    permission_classes = [IsAuthenticated, IsAdmin]

    def post(self, request):
        serializer = BroadcastNotificationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        title = serializer.validated_data["title"]
        message = serializer.validated_data["message"]

        from django.contrib.auth import get_user_model
        from apps.notifications.tasks import send_bulk_notification

        user_model = get_user_model()
        recipient_count = user_model.objects.filter(is_active=True).count()

        try:
            send_bulk_notification.delay(title=title, message=message)
        except Exception:
            send_bulk_notification(title=title, message=message)

        return api_success(
            data={"recipient_count": recipient_count},
            message="Broadcast notification queued successfully.",
            status_code=status.HTTP_202_ACCEPTED,
        )
