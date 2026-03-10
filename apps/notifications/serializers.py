from rest_framework import serializers

from apps.notifications.models import Notification


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = [
            "id",
            "notification_type",
            "title",
            "message",
            "is_read",
            "action_url",
            "created_at",
        ]
        read_only_fields = ["id", "notification_type", "title", "message", "action_url", "created_at"]


class BulkNotificationSerializer(serializers.Serializer):
    """Admin: send notification to all users or a role group."""
    notification_type = serializers.ChoiceField(
        choices=Notification.NotificationType.choices,
        default=Notification.NotificationType.ANNOUNCEMENT,
    )
    title = serializers.CharField(max_length=300)
    message = serializers.CharField()
    target_role = serializers.ChoiceField(
        choices=["all", "student", "instructor"],
        default="all",
    )
    action_url = serializers.CharField(max_length=500, required=False, default="")
