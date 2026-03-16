from rest_framework import serializers

from apps.notifications.models import Notification, NotificationPreference


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = [
            "id",
            "title",
            "message",
            "notification_type",
            "reference_id",
            "is_read",
            "created_at",
        ]
        read_only_fields = fields


class NotificationPreferenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationPreference
        fields = [
            "email_notifications_enabled",
            "in_app_notifications_enabled",
            "course_updates",
            "assignment_notifications",
            "quiz_notifications",
        ]


class BroadcastNotificationSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=300)
    message = serializers.CharField()
